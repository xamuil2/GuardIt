import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform, ScrollView, Alert, Dimensions, TextInput } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import WiFiService from '../services/WiFiService';
import NotificationService from '../services/NotificationService';

const { width, height } = Dimensions.get('window');

export default function IMUScreen() {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [arduinoIP, setArduinoIP] = useState('172.20.10.11');
  const [isPolling, setIsPolling] = useState(false);
  const [connectionRetries, setConnectionRetries] = useState(0);
  const [lastError, setLastError] = useState(null);
  const [connectedPort, setConnectedPort] = useState(null);
  const [notificationCount, setNotificationCount] = useState(0);
  const navigation = useNavigation();

  useEffect(() => {
    setIsConnected(WiFiService.getConnectionStatus());

    const updateNotificationCount = () => {
      setNotificationCount(NotificationService.getUnreadCount());
    };
    updateNotificationCount();
    
    const interval = setInterval(updateNotificationCount, 2000);

    return () => {
      WiFiService.stopPolling();
      clearInterval(interval);
    };
  }, []);

  const connectToArduino = async () => {
    setIsConnecting(true);
    setConnectionStatus('Connecting...');
    setLastError(null);
    
    WiFiService.setArduinoIP(arduinoIP);
    
    let success = false;
    let retries = 0;
    const maxRetries = 3;
    
    while (!success && retries < maxRetries) {
      if (retries > 0) {
        setConnectionStatus(`Retrying... (${retries}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
      
      success = await WiFiService.testConnection();
      retries++;
      
      if (!success && retries < maxRetries) {
        setConnectionRetries(retries);
      }
    }
    
    if (success) {
      setIsConnected(true);
      setConnectionStatus('Connected');
      setConnectionRetries(0);
      
      const baseURL = WiFiService.getBaseURL();
      const portMatch = baseURL.match(/:(\d+)/);
      if (portMatch) {
        setConnectedPort(portMatch[1]);
      }
      
      WiFiService.startPolling(500);
      setIsPolling(true);
    } else {
      setConnectionStatus('Connection failed');
      setLastError('Failed to connect after multiple attempts');
      
      Alert.alert(
        'Connection Error', 
        `Failed to connect to Arduino at ${arduinoIP}.\n\nPlease check:\n\n1. Arduino is powered on and connected to WiFi\n2. WiFi credentials are correct in Arduino code\n3. IP address is correct (check Serial Monitor)\n4. Both devices are on same WiFi network\n5. No firewall blocking port 80\n\nTried ${maxRetries} times.`,
        [
          { text: 'OK' },
          { 
            text: 'Try Again', 
            onPress: () => {
              setConnectionRetries(0);
              connectToArduino();
            }
          }
        ]
      );
    }
    
    setIsConnecting(false);
  };

  const disconnect = () => {
    WiFiService.stopPolling();
    setIsConnected(false);
    setIsPolling(false);
    setConnectionStatus('Disconnected');
    setConnectionRetries(0);
    setLastError(null);
    setConnectedPort(null);
  };

  const runNetworkDiagnostics = async () => {
    Alert.alert(
      'Network Diagnostics',
      'This will scan for Arduino devices and test connectivity.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Scan for Arduino', 
          onPress: async () => {
            setConnectionStatus('Scanning for Arduino...');
            
            try {
              const foundDevices = await scanForArduino();
              
              if (foundDevices.length > 0) {
                let deviceList = 'Found Arduino devices:\n\n';
                foundDevices.forEach((device, index) => {
                  deviceList += `${index + 1}. ${device.ip} - ${device.name}\n`;
                });
                
                Alert.alert(
                  'Arduino Found!', 
                  deviceList + '\nTap "Connect" to use the first device.',
                  [
                    { text: 'Cancel' },
                    { 
                      text: 'Connect', 
                      onPress: () => {
                        setArduinoIP(foundDevices[0].ip);
                        connectToArduino();
                      }
                    }
                  ]
                );
              } else {
                Alert.alert(
                  'No Arduino Found', 
                  'No Arduino devices found on the network.\n\nPlease check:\n• Arduino is powered on\n• Both devices are on same WiFi\n• Arduino code is uploaded and running\n\nTry scanning again or enter IP manually.'
                );
              }
            } catch (error) {
              Alert.alert('Scan Error', 'Failed to scan for Arduino devices');
            }
            
            setConnectionStatus('Disconnected');
          }
        }
      ]
    );
  };

  const scanForArduino = async () => {
    const foundDevices = [];
    
    const ipRanges = [
      '192.168.1',
      '192.168.0',
      '172.20.10',
      '10.0.0',
    ];
    
    for (const baseIP of ipRanges) {
      for (let i = 1; i <= 254; i++) {
        const testIP = `${baseIP}.${i}`;
        
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 1000);
          
          const response = await fetch(`http://${testIP}/status`, {
            method: 'GET',
            signal: controller.signal,
            headers: {
              'Accept': 'application/json',
            },
          });
          
          clearTimeout(timeoutId);
          
          if (response.ok) {
            const data = await response.json();
            
            if (data.name && data.name.includes('GuardIt')) {
              foundDevices.push({
                ip: testIP,
                name: data.name,
                version: data.version
              });
              break;
            }
          }
        } catch (error) {
          continue;
        }
      }
    }
    
    return foundDevices;
  };

  const togglePolling = () => {
    if (isPolling) {
      WiFiService.stopPolling();
      setIsPolling(false);
    } else {
      WiFiService.startPolling(500);
      setIsPolling(true);
    }
  };

  const testNotification = async () => {
    try {
      const result = await NotificationService.triggerLEDAlert();
      Alert.alert('Test Notification', 'Test notification sent successfully!');
    } catch (error) {
      Alert.alert('Test Failed', 'Failed to send test notification');
    }
  };

  return (
    <LinearGradient
      colors={['#0a0a0a', '#1a1a1a', '#2d1b1b']}
      style={styles.container}
    >
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton} 
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="arrow-back" size={24} color="white"/>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>IMU Sensor</Text>
        <View style={styles.headerSpacer} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.statusSection}>
          <LinearGradient
            colors={isConnected ? ['rgba(68, 255, 68, 0.2)', 'rgba(68, 255, 68, 0.1)'] : ['rgba(255, 68, 68, 0.2)', 'rgba(255, 68, 68, 0.1)']}
            style={styles.statusContainer}
          >
            <View style={styles.statusIconContainer}>
              <Ionicons 
                name={isConnected ? "wifi" : "wifi-outline"} 
                size={40} 
                color={isConnected ? "#44ff44" : "#ff4444"}
              />
            </View>
            <Text style={styles.statusTitle}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </Text>
            <Text style={styles.statusSubtitle}>{connectionStatus}</Text>
            
            {connectedPort && (
              <View style={styles.portIndicator}>
                <Ionicons name="wifi" size={16} color="#44ff44"/>
                <Text style={styles.portText}>Connected on port {connectedPort}</Text>
              </View>
            )}
            
            <View style={styles.notificationIndicator}>
              <Ionicons name="notifications" size={16} color="#ffaa00"/>
              <Text style={styles.notificationText}>
                {notificationCount} unread notification{notificationCount !== 1 ? 's' : ''}
              </Text>
            </View>
            
            {connectionRetries > 0 && (
              <View style={styles.retryIndicator}>
                <Ionicons name="refresh" size={16} color="#ffaa00"/>
                <Text style={styles.retryText}>Retry {connectionRetries}/3</Text>
              </View>
            )}
            
            {lastError && (
              <View style={styles.errorContainer}>
                <Ionicons name="alert-circle" size={16} color="#ff4444"/>
                <Text style={styles.errorText}>{lastError}</Text>
              </View>
            )}
            
            <View style={styles.ipInputContainer}>
              <Text style={styles.ipLabel}>Arduino IP Address:</Text>
              <TextInput
                style={styles.ipInput}
                value={arduinoIP}
                onChangeText={setArduinoIP}
                placeholder="172.20.10.11"
                placeholderTextColor="rgba(255, 255, 255, 0.5)"
                keyboardType="numeric"
              />
            </View>
            
            <View style={styles.connectionButtons}>
              {!isConnected ? (
                <TouchableOpacity 
                  style={[styles.connectButton, isConnecting && styles.connectingButton]} 
                  onPress={connectToArduino}
                  disabled={isConnecting}
                >
                  <LinearGradient
                    colors={isConnecting ? ['#666666', '#888888'] : ['#44ff44', '#66ff66']}
                    style={styles.buttonGradient}
                  >
                    <Ionicons name="wifi" size={20} color="white"/>
                    <Text style={styles.buttonText}>
                      {isConnecting ? 'Connecting...' : 'Connect to Arduino'}
                    </Text>
                  </LinearGradient>
                </TouchableOpacity>
              ) : (
                <TouchableOpacity style={styles.disconnectButton} onPress={disconnect}>
                  <LinearGradient
                    colors={['#ff4444', '#ff6666']}
                    style={styles.buttonGradient}
                  >
                    <Ionicons name="close" size={20} color="white"/>
                    <Text style={styles.buttonText}>Disconnect</Text>
                  </LinearGradient>
                </TouchableOpacity>
              )}
            </View>
          </LinearGradient>
        </View>
      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingBottom: 20,
    paddingHorizontal: 20,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
  },
  headerSpacer: {
    width: 40,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  statusSection: {
    marginBottom: 20,
  },
  statusContainer: {
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
  },
  statusIconContainer: {
    marginBottom: 10,
  },
  statusTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 5,
  },
  statusSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: 20,
  },
  ipInputContainer: {
    width: '100%',
    marginBottom: 20,
  },
  ipLabel: {
    fontSize: 16,
    color: 'white',
    marginBottom: 10,
    textAlign: 'center',
  },
  ipInput: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 10,
    paddingHorizontal: 15,
    paddingVertical: 12,
    fontSize: 16,
    color: 'white',
    textAlign: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  connectionButtons: {
    width: '100%',
  },
  connectButton: {
    borderRadius: 15,
    overflow: 'hidden',
    width: '100%',
  },
  connectingButton: {
    opacity: 0.7,
  },
  disconnectButton: {
    borderRadius: 15,
    overflow: 'hidden',
    width: '100%',
  },
  buttonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    paddingHorizontal: 20,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 15,
  },
  retryIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 170, 0, 0.2)',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 15,
  },
  retryText: {
    fontSize: 14,
    color: '#ffaa00',
    marginLeft: 8,
    fontWeight: 'bold',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 68, 68, 0.2)',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 15,
  },
  errorText: {
    fontSize: 14,
    color: '#ff4444',
    marginLeft: 8,
    fontWeight: 'bold',
  },
  portIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(68, 255, 68, 0.2)',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 15,
  },
  portText: {
    fontSize: 14,
    color: '#44ff44',
    marginLeft: 8,
    fontWeight: 'bold',
  },
  notificationIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 170, 0, 0.2)',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 15,
  },
  notificationText: {
    fontSize: 14,
    color: '#ffaa00',
    marginLeft: 8,
    fontWeight: 'bold',
  },
}); 
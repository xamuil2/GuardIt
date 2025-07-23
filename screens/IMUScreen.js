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
  const [arduinoIP, setArduinoIP] = useState('172.20.10.13:8080');
  const [connectionRetries, setConnectionRetries] = useState(0);
  const [lastError, setLastError] = useState(null);
  const [connectedPort, setConnectedPort] = useState(null);
  const [deviceType, setDeviceType] = useState('unknown');
  const [notificationCount, setNotificationCount] = useState(0);
  const navigation = useNavigation();

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const connected = await WiFiService.testConnection();
        setIsConnected(connected);
        setConnectionStatus(connected ? 'Connected' : 'Disconnected');
      } catch (error) {
        setIsConnected(false);
        setConnectionStatus('Connection failed');
      }
    };
    
    checkConnection();

    const initializeServices = async () => {
      await NotificationService.initialize();
    };
    initializeServices();

    const updateNotificationCount = () => {
      setNotificationCount(NotificationService.getUnreadCount());
    };
    updateNotificationCount();
    
    const interval = setInterval(updateNotificationCount, 2000);

    let lastBuzzerStatus = false;
    const pollBuzzer = async () => {
      try {
        const response = await fetch(`http://${arduinoIP}/buzzer/status`);
        if (response.ok) {
          const data = await response.json();
          const isActive = (data.buzzer && typeof data.buzzer.is_active !== 'undefined')
            ? data.buzzer.is_active
            : (typeof data.active !== 'undefined' ? data.active : false);
          if (isActive && !lastBuzzerStatus) {
            NotificationService.triggerBuzzerAlert();
          }
          lastBuzzerStatus = isActive;
        } else {
          console.log('Buzzer status fetch failed:', response.status);
        }
      } catch (error) {
        console.log('Buzzer polling error:', error);
      }
    };
    const buzzerInterval = setInterval(pollBuzzer, 2000);

    return () => {
      WiFiService.stopPolling();
      clearInterval(interval);
      clearInterval(buzzerInterval);
    };
  }, []);

  const connectToRaspberryPi = async () => {
    setIsConnecting(true);
    setConnectionStatus('Connecting...');
    setLastError(null);
    
    try {
    WiFiService.setArduinoIP(arduinoIP);
      const connected = await WiFiService.testConnection();
      
      if (connected) {
      setIsConnected(true);
        setConnectionStatus('Connected to Raspberry Pi');
      setConnectionRetries(0);
      
      WiFiService.startPolling(500);
    } else {
        setConnectionStatus('Connection failed');
        setConnectionRetries(prev => prev + 1);
        setLastError('Failed to connect to Raspberry Pi. Check IP address and network connection.');
      }
    } catch (error) {
      setConnectionStatus('Connection failed');
      setConnectionRetries(prev => prev + 1);
      setLastError(`Connection error: ${error.message}`);
    } finally {
    setIsConnecting(false);
    }
  };

  const disconnect = () => {
    WiFiService.stopPolling();
    setIsConnected(false);
    setConnectionStatus('Disconnected');
    setConnectionRetries(0);
    setLastError(null);
    setConnectedPort(null);
  };

  const runNetworkDiagnostics = async () => {
    Alert.alert(
      'Network Diagnostics',
      'This will scan for Raspberry Pi devices and test connectivity.',
      [
        {
          text: 'Cancel',
          style: 'cancel'
        },
        { 
          text: 'Scan for Raspberry Pi',
          onPress: async () => {
            setConnectionStatus('Scanning for Raspberry Pi...');
            
            try {
              const foundDevices = await scanForArduino();
              
              if (foundDevices.length > 0) {
                let deviceList = 'Found Raspberry Pi devices:\n\n';
                foundDevices.forEach(device => {
                  deviceList += `• ${device.name}\n   IP: ${device.ip}\n   Version: ${device.version}\n\n`;
                });
                
                Alert.alert(
                  'Raspberry Pi Found!',
                  deviceList + 'Would you like to connect to the first device?',
                  [
                    { text: 'Cancel', style: 'cancel' },
                    { 
                      text: 'Connect', 
                      onPress: () => {
                        setArduinoIP(foundDevices[0].ip);
                        connectToRaspberryPi();
                      }
                    }
                  ]
                );
              } else {
                Alert.alert(
                  'No Raspberry Pi Found',
                  'No Raspberry Pi devices found on the network.\n\nPlease check:\n• Raspberry Pi is powered on\n• Both devices are on same WiFi\n• Raspberry Pi server is running\n\nTry scanning again or enter IP manually.'
                );
              }
            } catch (error) {
              Alert.alert('Scan Error', 'Failed to scan for Raspberry Pi devices');
            }
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
        const testIP = `${baseIP}.${i}:8080`;
        
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 1000);
          
          const response = await fetch(`http://${testIP}/`, {
            method: 'GET',
            signal: controller.signal,
            headers: {
              'Accept': 'application/json',
            },
          });
          
          clearTimeout(timeoutId);
          
          if (response.ok) {
            const data = await response.json();
            
            if (data.title && data.title.includes('Raspberry Pi')) {
              foundDevices.push({
                ip: testIP,
                name: 'Raspberry Pi IoT Device',
                version: '1.0.0'
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
          <Text style={{ color: 'white', fontSize: 24, fontWeight: 'bold' }}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Raspberry Pi Connection</Text>
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
            
            {deviceType !== 'unknown' && (
              <View style={styles.deviceIndicator}>
                <Ionicons name={deviceType === 'raspberry-pi' ? "hardware-chip" : "flash"} size={16} color="#44ff44"/>
                <Text style={styles.deviceText}>
                  {deviceType === 'raspberry-pi' ? 'Raspberry Pi' : 'Arduino'} Device
                </Text>
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
              <Text style={styles.ipLabel}>Raspberry Pi IP Address:</Text>
              <TextInput
                style={styles.ipInput}
                value={arduinoIP}
                onChangeText={setArduinoIP}
                placeholder="10.103.186.99:8080"
                placeholderTextColor="rgba(255, 255, 255, 0.5)"
                keyboardType="numeric"
              />
            </View>
            
            <View style={styles.connectionButtons}>
              {!isConnected ? (
                <TouchableOpacity 
                  style={[styles.connectButton, isConnecting && styles.connectingButton]} 
                  onPress={connectToRaspberryPi}
                  disabled={isConnecting}
                >
                  <LinearGradient
                    colors={isConnecting ? ['#666666', '#888888'] : ['#44ff44', '#66ff66']}
                    style={styles.buttonGradient}
                  >
                    <Ionicons name="wifi" size={20} color="white"/>
                    <Text style={styles.connectButtonText}>
                      {isConnecting ? 'Connecting...' : 'Connect to Raspberry Pi'}
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
      {/* Debug: Test Notification Button */}
      <TouchableOpacity
        style={{ margin: 20, padding: 16, backgroundColor: '#ff4444', borderRadius: 12, alignItems: 'center' }}
        onPress={() => NotificationService.triggerBuzzerAlert()}
      >
        <Text style={{ color: 'white', fontWeight: 'bold' }}>Test Buzzer Notification</Text>
      </TouchableOpacity>
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
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
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
    gap: 10,
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
  deviceIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(68, 170, 255, 0.2)',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 15,
  },
  deviceText: {
    fontSize: 14,
    color: '#44aaff',
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
  connectButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  testButton: {
    borderRadius: 15,
    overflow: 'hidden',
    width: '100%',
  },
});

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform, Alert, TextInput } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import WiFiService from '../services/WiFiService';

export default function ConnectionScreen() {
  const [raspberryPiIP, setRaspberryPiIP] = useState('10.103.135.13:8080');
  const [cameraStreamIP, setCameraStreamIP] = useState('10.103.135.13:8080');
  const [isConnecting, setIsConnecting] = useState(false);
  const navigation = useNavigation();

  const handleConnect = async () => {
    if (!raspberryPiIP.trim() || !cameraStreamIP.trim()) {
      Alert.alert('Error', 'Please enter both IP addresses');
      return;
    }

    setIsConnecting(true);
    
    try {
      WiFiService.setArduinoIP(raspberryPiIP);
      
      const connected = await WiFiService.testConnection();
      
      if (connected) {
        Alert.alert(
          'Success', 
          'Successfully connected to both Raspberry Pi and Camera Stream!',
          [
            {
              text: 'Continue',
              onPress: () => {
                navigation.navigate('CameraStream', {
                  cameraIP: cameraStreamIP
                });
              }
            }
          ]
        );
      } else {
        Alert.alert('Connection Failed', 'Could not connect to Raspberry Pi. Please check the IP address and try again.');
      }
    } catch (error) {
      Alert.alert('Error', 'Connection failed: ' + error.message);
    } finally {
      setIsConnecting(false);
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
          <Text style={{ color: 'white', fontSize: 24, fontWeight: 'bold' }}>←</Text>
        </TouchableOpacity>
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>Connect Devices</Text>
          <Text style={styles.headerSubtitle}>Enter IP addresses to connect</Text>
        </View>
        <View style={styles.headerSpacer} />
      </View>

      <View style={styles.content}>
        <View style={styles.connectionCard}>
          <LinearGradient
            colors={['rgba(255, 255, 255, 0.08)', 'rgba(255, 255, 255, 0.03)']}
            style={styles.connectionCardGradient}
          >
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Raspberry Pi IP Address:</Text>
              <TextInput
                style={styles.ipInput}
                value={raspberryPiIP}
                onChangeText={setRaspberryPiIP}
                placeholder="10.103.135.13:8080"
                placeholderTextColor="rgba(255, 255, 255, 0.5)"
                keyboardType="url"
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Camera Stream IP Address:</Text>
              <TextInput
                style={styles.ipInput}
                value={cameraStreamIP}
                onChangeText={setCameraStreamIP}
                placeholder="10.103.139.13:8080"
                placeholderTextColor="rgba(255, 255, 255, 0.5)"
                keyboardType="url"
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <TouchableOpacity 
              style={[styles.connectButton, isConnecting && styles.connectingButton]} 
              onPress={handleConnect}
              disabled={isConnecting}
            >
              <LinearGradient
                colors={isConnecting ? ['#666666', '#888888'] : ['#44ff44', '#66ff66']}
                style={styles.connectButtonGradient}
              >
                <Ionicons name="wifi" size={20} color="white"/>
                <Text style={styles.connectButtonText}>
                  {isConnecting ? 'Connecting...' : 'Connect Devices'}
                </Text>
              </LinearGradient>
            </TouchableOpacity>
          </LinearGradient>
        </View>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingBottom: 20,
    backgroundColor: '#1a1a1a',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 68, 68, 0.15)',
  },
  backButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  headerContent: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    letterSpacing: 1,
    textShadowColor: 'rgba(255, 68, 68, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 4,
  },
  headerSpacer: {
    width: 44,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  connectionCard: {
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    shadowColor: '#ff4444',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
  },
  connectionCardGradient: {
    padding: 30,
    backgroundColor: 'transparent',
  },
  inputContainer: {
    marginBottom: 25,
  },
  inputLabel: {
    fontSize: 16,
    color: 'white',
    marginBottom: 10,
    fontWeight: '600',
  },
  ipInput: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    paddingHorizontal: 15,
    paddingVertical: 15,
    fontSize: 16,
    color: 'white',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  connectButton: {
    borderRadius: 15,
    overflow: 'hidden',
    marginTop: 10,
    shadowColor: '#44ff44',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
  },
  connectingButton: {
    opacity: 0.7,
  },
  connectButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    paddingHorizontal: 20,
  },
  connectButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
}); 
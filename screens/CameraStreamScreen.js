import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform, Alert, Dimensions, ScrollView } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { Image } from 'react-native';
import WiFiService from '../services/WiFiService';

const { width, height } = Dimensions.get('window');

export default function CameraStreamScreen({ route }) {
  const { cameraIP: initialCameraIP } = route.params || {};
  const [cameraIP, setCameraIP] = useState(initialCameraIP || '10.103.186.99:8080');
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [selectedCamera, setSelectedCamera] = useState('usb');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [streamError, setStreamError] = useState(null);
  const [cameraStatus, setCameraStatus] = useState(null);
  const [frameRate, setFrameRate] = useState(0);
  const [lastFrameTime, setLastFrameTime] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [detectionEnabled, setDetectionEnabled] = useState(false);
  const [detectionStatus, setDetectionStatus] = useState(null);
  const streamInterval = useRef(null);
  const navigation = useNavigation();

  useEffect(() => {
    checkConnection();
    checkCameraStatus();
    checkDetectionStatus();
    
    WiFiService.setSuspiciousActivityAlertCallback(handleSuspiciousActivityAlert);
    
    return () => {
      if (streamInterval.current) {
        clearInterval(streamInterval.current);
      }
      WiFiService.setSuspiciousActivityAlertCallback(null);
    };
  }, []);

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

  const checkCameraStatus = async () => {
    try {
      const response = await fetch(`http://${cameraIP}/status`);
      
      if (response.ok) {
        const data = await response.json();
        
        let cameraStatusData = null;
        
        if (data.camera_status) {
          cameraStatusData = data.camera_status;
        } else if (data.cameras) {
          cameraStatusData = data.cameras;
        } else if (data.csi_available !== undefined || data.usb_available !== undefined) {
          cameraStatusData = data;
        } else {
          for (const [key, value] of Object.entries(data)) {
            if (typeof value === 'object' && value !== null) {
              if (value.csi_available !== undefined || value.usb_available !== undefined) {
                cameraStatusData = value;
                break;
              }
            }
          }
        }
        
        setCameraStatus(cameraStatusData);
        
        if (cameraStatusData) {
        } else {
          setCameraStatus({
            csi_available: true,
            usb_available: true,
            usb_device_id: 0
          });
        }
      } else {
      }
    } catch (error) {
    }
  };

  const connectToCamera = async () => {
    setIsConnecting(true);
    setConnectionStatus('Connecting...');
    
    try {
      WiFiService.setArduinoIP(cameraIP);
      const connected = await WiFiService.testConnection();
      
      if (connected) {
        setIsConnected(true);
        setConnectionStatus('Connected');
        await checkCameraStatus();
      } else {
        setConnectionStatus('Connection failed');
        Alert.alert('Error', 'Failed to connect to Raspberry Pi camera server');
      }
    } catch (error) {
      setConnectionStatus('Connection failed');
      Alert.alert('Error', 'Connection failed: ' + error.message);
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnect = () => {
    stopStream();
    setIsConnected(false);
    setConnectionStatus('Disconnected');
    setCameraStatus(null);
    setCurrentFrame(null);
    setStreamError(null);
  };

  const startStream = async () => {
    if (!isConnected) {
      Alert.alert('Error', 'Please connect to the camera server first');
      return;
    }

    setIsStreaming(true);
    setStreamError(null);
    setIsLoading(true);
    
    await fetchCameraFrame();
    
    streamInterval.current = setInterval(fetchCameraFrame, 200);
  };

  const stopStream = () => {
    setIsStreaming(false);
    setIsLoading(false);
    if (streamInterval.current) {
      clearInterval(streamInterval.current);
      streamInterval.current = null;
    }
    setCurrentFrame(null);
    setStreamError(null);
  };

  const fetchCameraFrame = async () => {
    try {
      const timestamp = Date.now();
      let endpoint;
      
      if (selectedCamera === 'csi') {
        endpoint = `http://${cameraIP}/camera/csi?quality=80&width=640&height=480&format=jpeg&t=${timestamp}`;
      } else {
        endpoint = `http://${cameraIP}/camera/usb?quality=80&width=640&height=480&format=jpeg&t=${timestamp}`;
      }
      
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });

      if (response.ok) {
        const data = await response.json();
        
        if (data.success && data.image) {
          const imageUri = `data:image/jpeg;base64,${data.image}`;
          setCurrentFrame(imageUri);
          setIsLoading(false);
          
          const currentTime = Date.now();
          if (lastFrameTime > 0) {
            const timeDiff = currentTime - lastFrameTime;
            const fps = Math.round(1000 / timeDiff);
            setFrameRate(fps);
          }
          setLastFrameTime(currentTime);
        } else {
          setStreamError(data.error || 'Failed to get camera frame');
          setIsLoading(false);
        }
      } else {
        setStreamError(`HTTP ${response.status}: ${response.statusText}`);
        setIsLoading(false);
      }
      
    } catch (error) {
      setStreamError('Failed to fetch camera frame: ' + error.message);
      setIsLoading(false);
    }
  };

  const switchCamera = () => {
    const newCamera = selectedCamera === 'csi' ? 'usb' : 'csi';
    setSelectedCamera(newCamera);
    
    if (isStreaming) {
      stopStream();
      setTimeout(() => startStream(), 500);
    }
  };

  const toggleStream = () => {
    if (isStreaming) {
      stopStream();
    } else {
      startStream();
    }
  };

  const checkDetectionStatus = async () => {
    try {
      const status = await WiFiService.getDetectionStatus();
      setDetectionStatus(status);
      if (status && status.enabled !== undefined) {
        setDetectionEnabled(status.enabled);
      }
    } catch (error) {
    }
  };

  const enableDetection = async () => {
    try {
      const success = await WiFiService.enableDetection();
      if (success) {
        setDetectionEnabled(true);
        Alert.alert('Detection Enabled', 'Suspicious activity detection is now active');
      } else {
        Alert.alert('Error', 'Failed to enable detection');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to enable detection: ' + error.message);
    }
  };

  const disableDetection = async () => {
    try {
      const success = await WiFiService.disableDetection();
      if (success) {
        setDetectionEnabled(false);
        Alert.alert('Detection Disabled', 'Suspicious activity detection is now inactive');
      } else {
        Alert.alert('Error', 'Failed to disable detection');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to disable detection: ' + error.message);
    }
  };

  const toggleDetection = () => {
    if (detectionEnabled) {
      disableDetection();
    } else {
      enableDetection();
    }
  };

  const handleSuspiciousActivityAlert = (alertData) => {
    Alert.alert(
      alertData.title,
      alertData.message,
      [
        {
          text: 'OK',
          style: 'default',
          onPress: () => {
          }
        }
      ],
      { cancelable: false }
    );
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#1a1a2e', '#16213e', '#0f3460']}
        style={styles.gradient}
      >
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
            <Ionicons name="arrow-back" size={24} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Raspberry Pi Camera Stream</Text>
          <View style={styles.headerSpacer} />
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {}
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
              
              {!isConnected && (
                <TouchableOpacity 
                  style={[styles.connectButton, isConnecting && styles.connectingButton]} 
                  onPress={connectToCamera}
                  disabled={isConnecting}
                >
                  <LinearGradient
                    colors={isConnecting ? ['#666666', '#888888'] : ['#44ff44', '#66ff66']}
                    style={styles.buttonGradient}
                  >
                    <Ionicons name="wifi" size={20} color="white"/>
                    <Text style={styles.buttonText}>
                      {isConnecting ? 'Connecting...' : 'Connect to Camera Server'}
                    </Text>
                  </LinearGradient>
                </TouchableOpacity>
              )}
              
              {isConnected && (
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
            </LinearGradient>
          </View>

          {}
          {cameraStatus && (
            <View style={styles.cameraStatusContainer}>
              <Text style={styles.sectionTitle}>📹 Camera Status</Text>
              <View style={styles.statusRow}>
                <Text style={styles.statusLabel}>CSI Camera:</Text>
                <Text style={[styles.statusValue, { color: cameraStatus.csi_available ? '#4CAF50' : '#f44336' }]}>
                  {cameraStatus.csi_available ? 'Available' : 'Not Available'}
                </Text>
              </View>
              <View style={styles.statusRow}>
                <Text style={styles.statusLabel}>USB Camera:</Text>
                <Text style={[styles.statusValue, { color: cameraStatus.usb_available ? '#4CAF50' : '#f44336' }]}>
                  {cameraStatus.usb_available ? `Available (ID: ${cameraStatus.usb_device_id})` : 'Not Available'}
                </Text>
              </View>
            </View>
          )}

          {}
          {isConnected && (
            <View style={styles.cameraSelectionContainer}>
              <Text style={styles.sectionTitle}>📸 Select Camera</Text>
              <View style={styles.cameraButtons}>
                <TouchableOpacity 
                  style={[styles.cameraButton, selectedCamera === 'csi' && styles.activeCameraButton]}
                  onPress={() => setSelectedCamera('csi')}
                  disabled={!cameraStatus?.csi_available}
                >
                  <Ionicons 
                    name="camera" 
                    size={24} 
                    color={selectedCamera === 'csi' ? '#fff' : '#666'} 
                  />
                  <Text style={[styles.cameraButtonText, selectedCamera === 'csi' && styles.activeCameraButtonText]}>
                    CSI Camera
                  </Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  style={[styles.cameraButton, selectedCamera === 'usb' && styles.activeCameraButton]}
                  onPress={() => setSelectedCamera('usb')}
                  disabled={!cameraStatus?.usb_available}
                >
                  <Ionicons 
                    name="videocam" 
                    size={24} 
                    color={selectedCamera === 'usb' ? '#fff' : '#666'} 
                  />
                  <Text style={[styles.cameraButtonText, selectedCamera === 'usb' && styles.activeCameraButtonText]}>
                    USB Camera
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {}
          {isConnected && (
            <View style={styles.streamControlsContainer}>
              <Text style={styles.sectionTitle}>🎥 Stream Controls</Text>
              <TouchableOpacity 
                style={[styles.streamButton, isStreaming && styles.stopButton]} 
                onPress={toggleStream}
              >
                <LinearGradient
                  colors={isStreaming ? ['#ff4444', '#ff6666'] : ['#44ff44', '#66ff66']}
                  style={styles.buttonGradient}
                >
                  <Ionicons name={isStreaming ? "stop" : "play"} size={20} color="white"/>
                  <Text style={styles.buttonText}>
                    {isStreaming ? 'STOP STREAM' : 'START STREAM'}
                  </Text>
                </LinearGradient>
              </TouchableOpacity>

              {isStreaming && (
                <View style={styles.streamInfo}>
                  <Text style={styles.streamInfoText}>
                    Camera: {selectedCamera.toUpperCase()} | FPS: {frameRate}
                  </Text>
                </View>
              )}
            </View>
          )}

          {}
          {isConnected && (
            <View style={styles.detectionControlsContainer}>
              <Text style={styles.sectionTitle}>🔍 Suspicious Activity Detection</Text>
              <TouchableOpacity 
                style={[styles.detectionButton, detectionEnabled && styles.detectionActiveButton]} 
                onPress={toggleDetection}
              >
                <LinearGradient
                  colors={detectionEnabled ? ['#ff6b35', '#ff8c42'] : ['#666666', '#888888']}
                  style={styles.buttonGradient}
                >
                  <Ionicons name={detectionEnabled ? "eye" : "eye-off"} size={20} color="white"/>
                  <Text style={styles.buttonText}>
                    {detectionEnabled ? 'DETECTION ACTIVE' : 'ENABLE DETECTION'}
                  </Text>
                </LinearGradient>
              </TouchableOpacity>
              
              {detectionStatus && (
                <View style={styles.detectionInfo}>
                  <Text style={styles.detectionInfoText}>
                    Status: {detectionStatus.enabled ? 'Active' : 'Inactive'}
                    {detectionStatus.last_detection && ` | Last: ${new Date(detectionStatus.last_detection).toLocaleTimeString()}`}
                  </Text>
                </View>
              )}
            </View>
          )}

          {}
          <View style={styles.cameraContainer}>
            {currentFrame ? (
              <Image
                source={{ uri: currentFrame }}
                style={styles.cameraImage}
                resizeMode="contain"
                onError={(error) => {
                  setStreamError('Failed to load camera image');
                }}
              />
            ) : (
              <View style={styles.placeholderContainer}>
                <Ionicons name="camera" size={64} color="#666" />
                <Text style={styles.placeholderText}>
                  {isLoading ? 'Loading camera feed...' : 
                   isStreaming ? 'Connecting to camera...' : 'Camera not connected'}
                </Text>
                {streamError && (
                  <Text style={styles.errorText}>{streamError}</Text>
                )}
              </View>
            )}
          </View>
        </ScrollView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingBottom: 20,
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    flex: 1,
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
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
  cameraStatusContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 20,
    borderRadius: 15,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 15,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  statusLabel: {
    fontSize: 16,
    color: '#cccccc',
  },
  statusValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  cameraSelectionContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 20,
    borderRadius: 15,
    marginBottom: 20,
  },
  cameraButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  cameraButton: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    opacity: 0.5,
  },
  activeCameraButton: {
    backgroundColor: '#007AFF',
    opacity: 1,
  },
  cameraButtonText: {
    color: '#666',
    fontSize: 14,
    fontWeight: '600',
    marginTop: 5,
  },
  activeCameraButtonText: {
    color: '#fff',
  },
  streamControlsContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 20,
    borderRadius: 15,
    marginBottom: 20,
  },
  streamButton: {
    borderRadius: 15,
    overflow: 'hidden',
    marginBottom: 10,
  },
  stopButton: {
    backgroundColor: '#ff4444',
  },
  testButton: {
    borderRadius: 15,
    overflow: 'hidden',
    marginBottom: 10,
  },
  streamInfo: {
    alignItems: 'center',
  },
  streamInfoText: {
    color: '#fff',
    fontSize: 14,
  },
  cameraContainer: {
    backgroundColor: '#000',
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 20,
    minHeight: 300,
  },
  cameraImage: {
    width: '100%',
    height: 300,
    borderRadius: 12,
  },
  placeholderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    minHeight: 300,
    padding: 20,
  },
  placeholderText: {
    color: '#666',
    fontSize: 16,
    marginTop: 16,
    textAlign: 'center',
  },
  errorText: {
    color: '#ff4444',
    fontSize: 14,
    marginTop: 10,
    textAlign: 'center',
  },
  detectionControlsContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 20,
    borderRadius: 15,
    marginBottom: 20,
  },
  detectionButton: {
    borderRadius: 15,
    overflow: 'hidden',
    marginBottom: 10,
  },
  detectionActiveButton: {
    backgroundColor: '#ff6b35',
  },
  detectionInfo: {
    alignItems: 'center',
  },
  detectionInfoText: {
    color: '#fff',
    fontSize: 14,
  },
});

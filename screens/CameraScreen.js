import React, { useEffect, useState, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform, Alert, Dimensions, TextInput } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { WebView } from 'react-native-webview';
import CameraService from '../services/CameraService';

const { width, height } = Dimensions.get('window');

export default function CameraScreen() {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [motionDetected, setMotionDetected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [serverIP, setServerIP] = useState('192.168.1.100');
  const [streamURL, setStreamURL] = useState('');
  const [cameraSettings, setCameraSettings] = useState(null);
  const [detectionStats, setDetectionStats] = useState(null);
  const [screenshotCount, setScreenshotCount] = useState(0);
  const navigation = useNavigation();
  const motionCheckInterval = useRef(null);

  useEffect(() => {
    CameraService.setMotionCallback(() => {
      setMotionDetected(true);
      setTimeout(() => setMotionDetected(false), 5000);
    });

    checkConnectionStatus();

    return () => {
      CameraService.setMotionCallback(null);
      if (motionCheckInterval.current) {
        clearInterval(motionCheckInterval.current);
      }
    };
  }, []);

  const checkConnectionStatus = async () => {
    const connected = await CameraService.testConnection();
    setIsConnected(connected);
    setConnectionStatus(connected ? 'Connected' : 'Disconnected');
    
    if (connected) {
      const streaming = CameraService.getStreamingStatus();
      setIsStreaming(streaming);
      if (streaming) {
        setStreamURL(CameraService.getStreamURL());
      }
    }
  };

  const connectToCamera = async () => {
    setIsConnecting(true);
    setConnectionStatus('Connecting...');
    
    CameraService.setServerIP(serverIP);
    
    const success = await CameraService.testConnection();
    
    if (success) {
      setIsConnected(true);
      setConnectionStatus('Connected');
      
      const settings = await CameraService.getCameraSettings();
      setCameraSettings(settings);
      
      const stats = await CameraService.getDetectionStats();
      setDetectionStats(stats);
      
      startMotionMonitoring();
    } else {
      setConnectionStatus('Connection failed');
      Alert.alert(
        'Connection Error', 
        'Failed to connect to OpenCV camera server. Please check:\n\n1. OpenCV server is running on your computer\n2. IP address is correct\n3. Both devices are on same network\n4. Port 5000 is accessible'
      );
    }
    
    setIsConnecting(false);
  };

  const startCamera = async () => {
    const success = await CameraService.startCamera();
    if (success) {
      setIsStreaming(true);
      setStreamURL(CameraService.getStreamURL());
      setConnectionStatus('Streaming');
    } else {
      Alert.alert('Error', 'Failed to start camera stream');
    }
  };

  const stopCamera = async () => {
    const success = await CameraService.stopCamera();
    if (success) {
      setIsStreaming(false);
      setStreamURL('');
      setConnectionStatus('Connected');
    } else {
      Alert.alert('Error', 'Failed to stop camera stream');
    }
  };

  const startMotionMonitoring = () => {
    motionCheckInterval.current = setInterval(async () => {
      if (isConnected) {
        const motionData = await CameraService.getMotionDetection();
        if (motionData && motionData.motion_detected) {
          setMotionDetected(true);
          setTimeout(() => setMotionDetected(false), 5000);
        }
      }
    }, 2000);
  };

  const disconnect = () => {
    if (motionCheckInterval.current) {
      clearInterval(motionCheckInterval.current);
    }
    CameraService.destroy();
    setIsConnected(false);
    setIsStreaming(false);
    setMotionDetected(false);
    setConnectionStatus('Disconnected');
    setStreamURL('');
    setDetectionStats(null);
  };

  const takeScreenshot = async () => {
    try {
      const screenshot = await CameraService.takeScreenshot();
      if (screenshot && screenshot.success) {
        setScreenshotCount(prev => prev + 1);
        Alert.alert(
          'Screenshot Saved',
          `Screenshot captured successfully!\nTimestamp: ${screenshot.timestamp}`,
          [{ text: 'OK' }]
        );
      } else {
        Alert.alert('Error', 'Failed to capture screenshot');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to capture screenshot');
    }
  };

  const createStreamHTML = () => {
    return `
      <!DOCTYPE html>
      <html>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body {
              margin: 0;
              padding: 0;
              background: #000;
              display: flex;
              justify-content: center;
              align-items: center;
              height: 100vh;
            }
            .stream-container {
              width: 100%;
              height: 100%;
              display: flex;
              justify-content: center;
              align-items: center;
            }
            .stream-image {
              max-width: 100%;
              max-height: 100%;
              object-fit: contain;
            }
            .loading {
              color: white;
              font-family: Arial, sans-serif;
              font-size: 18px;
              text-align: center;
            }
          </style>
        </head>
        <body>
          <div class="stream-container">
            <img 
              src="${streamURL}" 
              class="stream-image" 
              alt="Camera Stream"
              onerror="this.style.display='none'; document.querySelector('.loading').style.display='block';"
            />
            <div class="loading" style="display: none;">
              Connecting to camera stream...
            </div>
          </div>
        </body>
      </html>
    `;
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
        <Text style={styles.headerTitle}>Live Camera</Text>
        <View style={styles.headerSpacer} />
      </View>

      <View style={styles.statusSection}>
        <LinearGradient
          colors={isConnected ? ['rgba(68, 255, 68, 0.2)', 'rgba(68, 255, 68, 0.1)'] : ['rgba(255, 68, 68, 0.2)', 'rgba(255, 68, 68, 0.1)']}
          style={styles.statusContainer}
        >
          <View style={styles.statusIconContainer}>
            <Ionicons 
              name={isConnected ? "videocam" : "videocam-outline"} 
              size={40} 
              color={isConnected ? "#44ff44" : "#ff4444"}
            />
          </View>
          <Text style={styles.statusTitle}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Text>
          <Text style={styles.statusSubtitle}>{connectionStatus}</Text>
          
          <View style={styles.ipInputContainer}>
            <Text style={styles.ipLabel}>OpenCV Server IP:</Text>
            <TextInput
              style={styles.ipInput}
              value={serverIP}
              onChangeText={setServerIP}
              placeholder="192.168.1.100"
              placeholderTextColor="rgba(255, 255, 255, 0.5)"
              keyboardType="numeric"
            />
          </View>
          
          <View style={styles.connectionButtons}>
            {!isConnected ? (
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
                    {isConnecting ? 'Connecting...' : 'Connect to Server'}
                  </Text>
                </LinearGradient>
              </TouchableOpacity>
            ) : (
              <View style={styles.connectedButtons}>
                {!isStreaming ? (
                  <TouchableOpacity style={styles.startButton} onPress={startCamera}>
                    <LinearGradient
                      colors={['#44ff44', '#66ff66']}
                      style={styles.buttonGradient}
                    >
                      <Ionicons name="play" size={20} color="white"/>
                      <Text style={styles.buttonText}>Start Stream</Text>
                    </LinearGradient>
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity style={styles.stopButton} onPress={stopCamera}>
                    <LinearGradient
                      colors={['#ffaa00', '#ffcc00']}
                      style={styles.buttonGradient}
                    >
                      <Ionicons name="pause" size={20} color="white"/>
                      <Text style={styles.buttonText}>Stop Stream</Text>
                    </LinearGradient>
                  </TouchableOpacity>
                )}
                
                <TouchableOpacity style={styles.disconnectButton} onPress={disconnect}>
                  <LinearGradient
                    colors={['#ff4444', '#ff6666']}
                    style={styles.buttonGradient}
                  >
                    <Ionicons name="close" size={20} color="white"/>
                    <Text style={styles.buttonText}>Disconnect</Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            )}
          </View>

          {isConnected && detectionStats && (
            <View style={styles.statsContainer}>
              <Text style={styles.statsTitle}>Detection Status</Text>
              <View style={styles.statsGrid}>
                <View style={styles.statItem}>
                  <Ionicons 
                    name={detectionStats.detection_model_loaded ? "checkmark-circle" : "close-circle"} 
                    size={24} 
                    color={detectionStats.detection_model_loaded ? "#44ff44" : "#ff4444"}
                  />
                  <Text style={styles.statText}>YOLOv8 Model</Text>
                </View>
                <View style={styles.statItem}>
                  <Ionicons 
                    name="people" 
                    size={24} 
                    color="#44ff44"
                  />
                  <Text style={styles.statText}>{detectionStats.active_tracks} Tracks</Text>
                </View>
                <View style={styles.statItem}>
                  <Ionicons 
                    name="camera" 
                    size={24} 
                    color="#44ff44"
                  />
                  <Text style={styles.statText}>{detectionStats.camera_settings?.fps || 30} FPS</Text>
                </View>
              </View>
            </View>
          )}
        </LinearGradient>
      </View>

      {motionDetected && (
        <View style={styles.motionAlert}>
          <LinearGradient
            colors={['rgba(255, 68, 68, 0.25)', 'rgba(255, 68, 68, 0.15)']}
            style={styles.alertContainer}
          >
            <Ionicons name="warning" size={24} color="#ff4444"/>
            <Text style={styles.alertText}>Motion Detected!</Text>
          </LinearGradient>
        </View>
      )}

      {isStreaming && streamURL ? (
        <View style={styles.streamContainer}>
          <WebView
            source={{ html: createStreamHTML() }}
            style={styles.webview}
            javaScriptEnabled={true}
            domStorageEnabled={true}
            startInLoadingState={true}
            scalesPageToFit={true}
            allowsInlineMediaPlayback={true}
            mediaPlaybackRequiresUserAction={false}
          />
          
          <TouchableOpacity style={styles.screenshotButton} onPress={takeScreenshot}>
            <LinearGradient
              colors={['rgba(0, 0, 0, 0.7)', 'rgba(0, 0, 0, 0.5)']}
              style={styles.screenshotButtonGradient}
            >
              <Ionicons name="camera" size={24} color="white"/>
              <Text style={styles.screenshotButtonText}>Screenshot</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.placeholderContainer}>
          <LinearGradient
            colors={['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']}
            style={styles.placeholder}
          >
            <Ionicons name="videocam-outline" size={80} color="rgba(255, 255, 255, 0.3)"/>
            <Text style={styles.placeholderText}>
              {isConnected ? 'Tap "Start Stream" to view camera feed' : 'Connect to OpenCV server to view camera feed'}
            </Text>
          </LinearGradient>
        </View>
      )}

      {!isConnected && (
        <View style={styles.instructionsSection}>
          <Text style={styles.sectionTitle}>Setup Instructions</Text>
          <LinearGradient
            colors={['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']}
            style={styles.instructionsContainer}
          >
            <Text style={styles.instructionText}>
              1. Start the OpenCV server on your computer{'\n'}
              2. Note the computer's IP address{'\n'}
              3. Enter the IP address above and tap "Connect"{'\n'}
              4. Tap "Start Stream" to view live camera feed{'\n'}
              5. Motion detection alerts will be sent automatically
            </Text>
          </LinearGradient>
        </View>
      )}
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
  statusSection: {
    paddingHorizontal: 20,
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
  },
  connectingButton: {
    opacity: 0.7,
  },
  connectedButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
  },
  startButton: {
    borderRadius: 15,
    overflow: 'hidden',
    flex: 1,
    marginRight: 10,
  },
  stopButton: {
    borderRadius: 15,
    overflow: 'hidden',
    flex: 1,
    marginRight: 10,
  },
  disconnectButton: {
    borderRadius: 15,
    overflow: 'hidden',
    flex: 1,
    marginLeft: 10,
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
  motionAlert: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  alertContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 15,
    padding: 15,
  },
  alertText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  streamContainer: {
    flex: 1,
    marginHorizontal: 20,
    marginBottom: 20,
    borderRadius: 15,
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  webview: {
    flex: 1,
    backgroundColor: '#000',
  },
  placeholderContainer: {
    flex: 1,
    marginHorizontal: 20,
    marginBottom: 20,
  },
  placeholder: {
    flex: 1,
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  placeholderText: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 16,
    textAlign: 'center',
    marginTop: 20,
    lineHeight: 24,
  },
  instructionsSection: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 15,
  },
  instructionsContainer: {
    borderRadius: 15,
    padding: 20,
  },
  instructionText: {
    fontSize: 16,
    color: 'white',
    lineHeight: 24,
  },
  statsContainer: {
    marginTop: 15,
    paddingHorizontal: 10,
  },
  statsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 10,
    textAlign: 'center',
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
    paddingHorizontal: 10,
  },
  statText: {
    fontSize: 12,
    color: 'white',
    marginTop: 5,
    textAlign: 'center',
  },
  screenshotButton: {
    position: 'absolute',
    top: 20,
    right: 20,
    borderRadius: 20,
    overflow: 'hidden',
  },
  screenshotButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 15,
  },
  screenshotButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: 8,
  },
}); 
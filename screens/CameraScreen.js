import React, { useEffect, useState, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform, Alert, Dimensions, TextInput, Image, ScrollView } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { WebView } from 'react-native-webview';
import WiFiService from '../services/WiFiService';
import CameraService from '../services/CameraService';

const { width, height } = Dimensions.get('window');

export default function CameraScreen() {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [motionDetected, setMotionDetected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [serverIP, setServerIP] = useState('172.20.10.14:8090');
  const [streamURL, setStreamURL] = useState('');
  const [cameraSettings, setCameraSettings] = useState(null);
  const [detectionStats, setDetectionStats] = useState(null);
  const [screenshotCount, setScreenshotCount] = useState(0);
  
  // New Raspberry Pi camera states
  const [cameraStatus, setCameraStatus] = useState(null);
  const [lastImage, setLastImage] = useState(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [streamFrame, setStreamFrame] = useState(null);
  const [useNewCamera, setUseNewCamera] = useState(true); // Toggle between old and new camera system
  
  const navigation = useNavigation();
  const motionCheckInterval = useRef(null);
  const streamInterval = useRef(null);

  useEffect(() => {
    CameraService.setMotionCallback(() => {
      setMotionDetected(true);
      setTimeout(() => setMotionDetected(false), 5000);
    });

    checkConnectionStatus();
    
    // Check WiFi connection and load camera status
    setIsConnected(WiFiService.getConnectionStatus());
    if (WiFiService.getConnectionStatus() && useNewCamera) {
      loadCameraStatus();
    }

    return () => {
      CameraService.setMotionCallback(null);
      if (motionCheckInterval.current) {
        clearInterval(motionCheckInterval.current);
      }
      if (streamInterval.current) {
        clearInterval(streamInterval.current);
      }
    };
  }, [useNewCamera]);

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
        'Failed to connect to OpenCV camera server. Please check:\n\n1. OpenCV server is running on your computer\n2. IP address is correct\n3. Both devices are on same network\n4. Port 8090 is accessible'
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
    if (streamInterval.current) {
      clearInterval(streamInterval.current);
    }
    CameraService.destroy();
    setIsConnected(false);
    setIsStreaming(false);
    setMotionDetected(false);
    setConnectionStatus('Disconnected');
    setStreamURL('');
    setDetectionStats(null);
    
    // Reset new camera states
    setLastImage(null);
    setStreamFrame(null);
    setCameraStatus(null);
  };

  // New Raspberry Pi camera functions
  const loadCameraStatus = async () => {
    try {
      const status = await WiFiService.getCameraStatus();
      setCameraStatus(status);
    } catch (error) {
      console.log('Failed to load camera status:', error);
    }
  };

  const captureCSI = async () => {
    if (!isConnected) {
      Alert.alert('Not Connected', 'Please connect to the Raspberry Pi first');
      return;
    }

    setIsCapturing(true);
    try {
      const result = await WiFiService.captureCSIImage();
      if (result.success) {
        setLastImage({
          type: 'CSI',
          data: result.image,
          timestamp: result.timestamp
        });
      } else {
        Alert.alert('Capture Failed', result.error || 'Failed to capture CSI image');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to capture CSI image');
    } finally {
      setIsCapturing(false);
    }
  };

  const captureUSB = async () => {
    if (!isConnected) {
      Alert.alert('Not Connected', 'Please connect to the Raspberry Pi first');
      return;
    }

    setIsCapturing(true);
    try {
      const result = await WiFiService.captureUSBImage();
      if (result.success) {
        setLastImage({
          type: 'USB',
          data: result.image,
          timestamp: result.timestamp
        });
      } else {
        Alert.alert('Capture Failed', result.error || 'Failed to capture USB image');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to capture USB image');
    } finally {
      setIsCapturing(false);
    }
  };

  const captureBoth = async () => {
    if (!isConnected) {
      Alert.alert('Not Connected', 'Please connect to the Raspberry Pi first');
      return;
    }

    setIsCapturing(true);
    try {
      const result = await WiFiService.captureBothImages();
      if (result.cameras) {
        setLastImage({
          type: 'Both',
          data: result.cameras,
          timestamp: result.timestamp
        });
      } else {
        Alert.alert('Capture Failed', 'Failed to capture from both cameras');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to capture from both cameras');
    } finally {
      setIsCapturing(false);
    }
  };

  const toggleNewCameraStreaming = async () => {
    if (!isConnected) {
      Alert.alert('Not Connected', 'Please connect to the Raspberry Pi first');
      return;
    }

    if (isStreaming) {
      // Stop streaming
      try {
        await WiFiService.stopCameraStream();
        setIsStreaming(false);
        setStreamFrame(null);
        if (streamInterval.current) {
          clearInterval(streamInterval.current);
        }
      } catch (error) {
        Alert.alert('Error', 'Failed to stop streaming');
      }
    } else {
      // Start streaming
      try {
        const result = await WiFiService.startCameraStream();
        if (result.success) {
          setIsStreaming(true);
          startNewStreamingFrames();
        } else {
          Alert.alert('Streaming Failed', result.error || 'Failed to start streaming');
        }
      } catch (error) {
        Alert.alert('Error', 'Failed to start streaming');
      }
    }
  };

  const startNewStreamingFrames = () => {
    streamInterval.current = setInterval(async () => {
      if (!isStreaming) {
        clearInterval(streamInterval.current);
        return;
      }

      try {
        const frame = await WiFiService.getStreamFrame();
        if (frame.success) {
          setStreamFrame(frame.frame);
        }
      } catch (error) {
        // Silently fail for streaming frames
      }
    }, 200); // 5 FPS
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

      {/* Camera System Toggle */}
      <View style={styles.toggleSection}>
        <Text style={styles.toggleTitle}>Camera System:</Text>
        <View style={styles.toggleContainer}>
          <TouchableOpacity 
            style={[styles.toggleButton, !useNewCamera && styles.toggleButtonActive]}
            onPress={() => setUseNewCamera(false)}
          >
            <Text style={[styles.toggleText, !useNewCamera && styles.toggleTextActive]}>OpenCV Server</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.toggleButton, useNewCamera && styles.toggleButtonActive]}
            onPress={() => setUseNewCamera(true)}
          >
            <Text style={[styles.toggleText, useNewCamera && styles.toggleTextActive]}>Raspberry Pi Camera</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* New Raspberry Pi Camera System */}
      {useNewCamera && (
        <ScrollView style={styles.newCameraSection} showsVerticalScrollIndicator={false}>
          {/* Camera Status */}
          {cameraStatus && (
            <View style={styles.cameraStatusContainer}>
              <Text style={styles.sectionTitle}>📹 Camera Status</Text>
              <View style={styles.statusRow}>
                <Text style={styles.statusLabel}>CSI Camera:</Text>
                <Text style={[styles.statusValue, { color: cameraStatus.camera_status?.csi_available ? '#4CAF50' : '#f44336' }]}>
                  {cameraStatus.camera_status?.csi_available ? 'Available' : 'Not Available'}
                </Text>
              </View>
              <View style={styles.statusRow}>
                <Text style={styles.statusLabel}>USB Camera:</Text>
                <Text style={[styles.statusValue, { color: cameraStatus.camera_status?.usb_available ? '#4CAF50' : '#f44336' }]}>
                  {cameraStatus.camera_status?.usb_available ? `Available (ID: ${cameraStatus.camera_status?.usb_device_id})` : 'Not Available'}
                </Text>
              </View>
            </View>
          )}

          {/* Camera Controls */}
          <View style={styles.controlsContainer}>
            <Text style={styles.sectionTitle}>📸 Camera Controls</Text>
            
            <TouchableOpacity
              style={[styles.button, (!isConnected || !cameraStatus?.camera_status?.csi_available) && styles.buttonDisabled]}
              onPress={captureCSI}
              disabled={!isConnected || !cameraStatus?.camera_status?.csi_available || isCapturing}
            >
              <Ionicons name="camera" size={20} color="#ffffff" />
              <Text style={styles.buttonText}>
                {isCapturing ? 'Capturing...' : 'Capture CSI Camera'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.button, (!isConnected || !cameraStatus?.camera_status?.usb_available) && styles.buttonDisabled]}
              onPress={captureUSB}
              disabled={!isConnected || !cameraStatus?.camera_status?.usb_available || isCapturing}
            >
              <Ionicons name="videocam" size={20} color="#ffffff" />
              <Text style={styles.buttonText}>
                {isCapturing ? 'Capturing...' : 'Capture USB Camera'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.button, (!isConnected || !cameraStatus?.available_endpoints?.dual_capture) && styles.buttonDisabled]}
              onPress={captureBoth}
              disabled={!isConnected || !cameraStatus?.available_endpoints?.dual_capture || isCapturing}
            >
              <Ionicons name="albums" size={20} color="#ffffff" />
              <Text style={styles.buttonText}>
                {isCapturing ? 'Capturing...' : 'Capture Both Cameras'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.button, styles.streamButton, (!isConnected || !cameraStatus?.camera_status?.usb_available) && styles.buttonDisabled]}
              onPress={toggleNewCameraStreaming}
              disabled={!isConnected || !cameraStatus?.camera_status?.usb_available}
            >
              <Ionicons name={isStreaming ? "stop" : "play"} size={20} color="#ffffff" />
              <Text style={styles.buttonText}>
                {isStreaming ? 'Stop Streaming' : 'Start Live Stream'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Live Stream */}
          {isStreaming && streamFrame && (
            <View style={styles.streamContainer}>
              <Text style={styles.imageTitle}>Live Stream (USB Camera)</Text>
              <Image 
                source={{ uri: `data:image/jpeg;base64,${streamFrame}` }}
                style={styles.streamImage}
                resizeMode="contain"
              />
            </View>
          )}

          {/* Last Captured Image */}
          {lastImage && (
            <View style={styles.imageContainer}>
              <Text style={styles.imageTitle}>
                {lastImage.type === 'Both' ? 'Dual Camera Capture' : `${lastImage.type} Camera`}
              </Text>
              
              {lastImage.type === 'Both' ? (
                <View style={styles.dualImageContainer}>
                  {lastImage.data.csi && lastImage.data.csi.success && (
                    <View style={styles.singleImageContainer}>
                      <Text style={styles.cameraLabel}>CSI Camera</Text>
                      <Image 
                        source={{ uri: `data:image/jpeg;base64,${lastImage.data.csi.image}` }}
                        style={styles.smallImage}
                        resizeMode="contain"
                      />
                    </View>
                  )}
                  {lastImage.data.usb && lastImage.data.usb.success && (
                    <View style={styles.singleImageContainer}>
                      <Text style={styles.cameraLabel}>USB Camera</Text>
                      <Image 
                        source={{ uri: `data:image/jpeg;base64,${lastImage.data.usb.image}` }}
                        style={styles.smallImage}
                        resizeMode="contain"
                      />
                    </View>
                  )}
                </View>
              ) : (
                <Image 
                  source={{ uri: `data:image/jpeg;base64,${lastImage.data}` }}
                  style={styles.fullImage}
                  resizeMode="contain"
                />
              )}
            </View>
          )}
        </ScrollView>
      )}

      {/* Old OpenCV Camera System */}
      {!useNewCamera && (
        <View style={styles.oldCameraSection}>

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
  // New styles for camera system toggle
  toggleSection: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  toggleTitle: {
    fontSize: 16,
    color: 'white',
    marginBottom: 10,
    textAlign: 'center',
  },
  toggleContainer: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 10,
    padding: 2,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  toggleButtonActive: {
    backgroundColor: 'rgba(68, 255, 68, 0.3)',
  },
  toggleText: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 14,
    fontWeight: '600',
  },
  toggleTextActive: {
    color: '#44ff44',
  },
  // New camera system styles
  newCameraSection: {
    flex: 1,
    paddingHorizontal: 20,
  },
  oldCameraSection: {
    flex: 1,
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
  controlsContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 20,
    borderRadius: 15,
    marginBottom: 20,
  },
  button: {
    backgroundColor: '#007AFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 15,
    borderRadius: 10,
    marginBottom: 15,
  },
  streamButton: {
    backgroundColor: '#FF6B35',
  },
  buttonDisabled: {
    backgroundColor: '#666666',
    opacity: 0.6,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 10,
  },
  imageContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 20,
    borderRadius: 15,
    marginBottom: 20,
  },
  streamContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 20,
    borderRadius: 15,
    marginBottom: 20,
  },
  imageTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 15,
    textAlign: 'center',
  },
  fullImage: {
    width: width - 80,
    height: 200,
    borderRadius: 10,
    alignSelf: 'center',
  },
  streamImage: {
    width: width - 80,
    height: 180,
    borderRadius: 10,
    alignSelf: 'center',
  },
  dualImageContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  singleImageContainer: {
    flex: 1,
    marginHorizontal: 5,
  },
  cameraLabel: {
    fontSize: 14,
    color: '#cccccc',
    textAlign: 'center',
    marginBottom: 10,
  },
  smallImage: {
    width: '100%',
    height: 120,
    borderRadius: 10,
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
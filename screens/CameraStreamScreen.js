import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform, FlatList, Dimensions, Image, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import NotificationService from '../services/NotificationService';

const { width, height } = Dimensions.get('window');

export default function CameraStreamScreen({ route }) {
  const { cameraIP: initialCameraIP } = route.params || {};
  const [cameraIP] = useState(initialCameraIP || '10.103.139.13:8080');
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [isConnected, setIsConnected] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const navigation = useNavigation();

  useEffect(() => {
    setNotifications(NotificationService.getNotifications());
    let lastBuzzerStatus = false;
    const pollBuzzer = async () => {
      try {
        const response = await fetch(`http://${cameraIP}/buzzer/status`);
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

    let streamInterval = null;
    const fetchCameraFrame = async () => {
      try {
        let endpoint = selectedCamera === 'csi'
          ? `http://${cameraIP}/camera/csi?quality=80&width=640&height=480&format=jpeg&t=${Date.now()}`
          : `http://${cameraIP}/camera/usb?quality=80&width=640&height=480&format=jpeg&t=${Date.now()}`;
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
            setCurrentFrame(`data:image/jpeg;base64,${data.image}`);
            if (data.alertType === 'object_close' || data.alert === true) {
              Alert.alert('Warning', 'An object is getting close to the camera!');
            }
          } else {
            setCurrentFrame(null);
          }
        } else {
          setCurrentFrame(null);
        }
      } catch (error) {
        console.log('Camera frame fetch error:', error);
        setCurrentFrame(null);
      }
    };
    if (selectedCamera && isStreaming && isConnected) {
      fetchCameraFrame();
      streamInterval = setInterval(fetchCameraFrame, 83);
    }

    let lastSuspicious = false;
    const pollSuspicious = async () => {
      try {
        const response = await fetch(`http://${cameraIP}/detection/status`);
        if (response.ok) {
          const data = await response.json();
          const suspicious = data.suspicious === true || (data.status && data.status.suspicious === true) || (data.enabled && data.person_detected === true);
          if (suspicious && !lastSuspicious) {
            NotificationService.triggerSuspiciousActivityAlert();
          }
          lastSuspicious = suspicious;
        } else {
          console.log('Suspicious detection fetch failed:', response.status);
        }
      } catch (error) {
        console.log('Suspicious detection polling error:', error);
      }
    };
    const suspiciousInterval = setInterval(pollSuspicious, 2000);

    return () => {
      clearInterval(buzzerInterval);
      if (streamInterval) clearInterval(streamInterval);
      clearInterval(suspiciousInterval);
    };
  }, [cameraIP, selectedCamera, isStreaming, isConnected]);

  useEffect(() => {
    if (selectedCamera) {
      setIsStreaming(true);
      return () => setIsStreaming(false);
    }
  }, [selectedCamera]);

  const renderNotification = ({ item }) => (
    <TouchableOpacity
      style={[styles.notificationItem, !item.read && styles.unreadNotification]}
    >
      <LinearGradient
        colors={item.read ? 
          ['rgba(255, 255, 255, 0.05)', 'rgba(255, 255, 255, 0.02)'] : 
          ['rgba(255, 68, 68, 0.15)', 'rgba(255, 68, 68, 0.05)']
        }
        style={styles.notificationGradient}
      >
        <View style={styles.notificationHeader}>
          <View style={styles.notificationIcon}>
            <Ionicons 
              name={
                item.type === 'led_alert' ? 'warning' : 
                item.type === 'suspicious_activity' ? 'eye' : 
                'notifications'
              } 
              size={24} 
              color={item.read ? '#888' : '#ff4444'}
            />
            {!item.read && <View style={styles.unreadDot} />}
          </View>
          <View style={styles.notificationContent}>
            <Text style={[styles.notificationTitle, item.read && styles.readText]}>
              {item.title}
            </Text>
            <Text style={[styles.notificationBody, item.read && styles.readText]}>
              {item.body}
            </Text>
            <View style={styles.notificationMeta}>
              <Text style={[styles.notificationTime, item.read && styles.readText]}>
                {NotificationService.formatTimestamp(item.timestamp)}
              </Text>
            </View>
          </View>
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );

  return (
      <LinearGradient
        colors={['#0a0a0a', '#1a1a1a', '#2d1b1b']}
      style={styles.container}
      >
      {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
          <Text style={{ color: 'white', fontSize: 24, fontWeight: 'bold' }}>←</Text>
          </TouchableOpacity>
          <View style={styles.headerContent}>
            <Text style={styles.headerTitle}>Camera Stream</Text>
          </View>
          <View style={styles.headerSpacer} />
        </View>

      {/* Camera Selector */}
      <View style={styles.cameraSelectorRow}>
                <TouchableOpacity 
          style={[styles.cameraSelectorButton, selectedCamera === 'usb' && styles.cameraSelectorButtonActive]}
          onPress={() => setSelectedCamera('usb')}
        >
          <Text style={[styles.cameraSelectorText, selectedCamera === 'usb' && styles.cameraSelectorTextActive]}>Front</Text>
                </TouchableOpacity>
                  <TouchableOpacity 
          style={[styles.cameraSelectorButton, selectedCamera === 'csi' && styles.cameraSelectorButtonActive]}
                    onPress={() => setSelectedCamera('csi')}
        >
          <Text style={[styles.cameraSelectorText, selectedCamera === 'csi' && styles.cameraSelectorTextActive]}>Back</Text>
                  </TouchableOpacity>
                </View>

      {/* Camera Stream Area */}
      <View style={styles.cameraStreamBox}>
        {selectedCamera && isStreaming && isConnected && currentFrame ? (
          <Image source={{ uri: currentFrame }} style={styles.cameraImage} resizeMode="contain" />
        ) : (
          <View style={styles.cameraStreamPlaceholder}>
            <Ionicons name="videocam" size={48} color="#888" />
            <Text style={styles.cameraStreamPlaceholderText}>
              {selectedCamera ? 'Camera Stream' : 'Select a camera to view stream'}
            </Text>
          </View>
        )}
      </View>

      {/* Notifications Section (bottom half, scrollable) */}
      <View style={styles.notificationsSection}>
        <Text style={styles.notificationsTitle}>Notifications</Text>
        <FlatList
          data={notifications}
          renderItem={renderNotification}
          keyExtractor={item => item.id}
          showsVerticalScrollIndicator={true}
          contentContainerStyle={styles.notificationsList}
        />
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
    alignItems: 'center',
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
  headerSpacer: {
    width: 44,
  },
  cameraSelectorRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 18,
    marginBottom: 10,
    gap: 16,
  },
  cameraSelectorButton: {
    paddingVertical: 10,
    paddingHorizontal: 32,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.07)',
    marginHorizontal: 8,
  },
  cameraSelectorButtonActive: {
    backgroundColor: '#ff4444',
  },
  cameraSelectorText: {
    color: '#aaa',
    fontSize: 16,
    fontWeight: '600',
  },
  cameraSelectorTextActive: {
    color: 'white',
  },
  cameraStreamBox: {
    height: height * 0.28,
    marginHorizontal: 20,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.07)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  cameraImage: {
    width: '100%',
    height: '100%',
    borderRadius: 18,
  },
  cameraStreamPlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cameraStreamPlaceholderText: {
    color: '#888',
    fontSize: 18,
    marginTop: 8,
  },
  notificationsSection: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.12)',
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    paddingTop: 12,
    paddingHorizontal: 10,
    marginTop: 6,
  },
  notificationsTitle: {
    color: '#ff4444',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
    marginLeft: 6,
  },
  notificationsList: {
    paddingBottom: 20,
  },
  notificationItem: {
    marginBottom: 12,
    borderRadius: 15,
    overflow: 'hidden',
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: 'rgba(255, 68, 68, 0.15)',
    shadowColor: '#ff4444',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
  },
  unreadNotification: {
    borderWidth: 2,
    borderColor: '#ff4444',
    backgroundColor: 'rgba(255, 68, 68, 0.08)',
  },
  notificationGradient: {
    padding: 16,
    backgroundColor: 'transparent',
  },
  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  notificationIcon: {
    marginRight: 15,
    position: 'relative',
  },
  unreadDot: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#ff4444',
  },
  notificationContent: {
    flex: 1,
  },
  notificationTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 5,
    letterSpacing: 0.5,
  },
  notificationBody: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.85)',
    marginBottom: 10,
    lineHeight: 20,
  },
  notificationMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  notificationTime: {
    fontSize: 12,
    color: '#ff4444',
    fontWeight: 'bold',
  },
  readText: {
    color: 'rgba(255, 255, 255, 0.5)',
  },
});



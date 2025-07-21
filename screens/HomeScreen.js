import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform, ScrollView, Alert, Dimensions, Linking, TextInput } from 'react-native';
import { signOut } from 'firebase/auth';
import { auth } from '../firebase';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import NotificationService from '../services/NotificationService';

const { width, height } = Dimensions.get('window');
export default function HomeScreen() {
  const [expoPushToken, setExpoPushToken] = useState('');
  const [notification, setNotification] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notificationService] = useState(NotificationService);
  const navigation = useNavigation();

  useEffect(() => {
    registerForPushNotificationsAsync().then(token => setExpoPushToken(token));
    const subscription = Notifications.addNotificationReceivedListener(notification => {
      setNotification(notification);
    });
    
    notificationService.initialize();
    
    const loadUnreadCount = () => {
      setUnreadCount(notificationService.getUnreadCount());
    };
    loadUnreadCount();
    
    const interval = setInterval(loadUnreadCount, 5000);
    
    return () => {
      subscription.remove();
      clearInterval(interval);
    };
  }, [notificationService]);

  const handleLogout = async () => {
    try {
      await signOut(auth);
    } catch (error) {
    }
  };

  const [cameraIP, setCameraIP] = useState('10.103.186.99:8080');

  const openCameraStream = () => {
    navigation.navigate('CameraStream', { cameraIP });
  };

  return (
    <LinearGradient
      colors={['#0a0a0a', '#1a1a1a', '#2d1b1b']}
      style={styles.container}
    >
      <View style={styles.header}>
        <View style={styles.logoContainer}>
          <View style={styles.logoBackground}>
            <Ionicons name="shield-checkmark" size={48} color="#ff4444"/>
          </View>
          <View style={styles.logoTextContainer}>
            <Text style={styles.logoText}>GuardIt</Text>
            <Text style={styles.subtitle}>SECURITY SYSTEM</Text>
          </View>
        </View>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.welcomeContainer}>
          <Text style={styles.welcomeTitle}>Welcome Back!</Text>
          <Text style={styles.welcomeSubtitle}>Your security system is active and monitoring</Text>
        </View>

        <View style={styles.alertSection}>
          <LinearGradient
            colors={['rgba(255, 68, 68, 0.2)', 'rgba(255, 68, 68, 0.1)']}
            style={styles.alertContainer}
          >
            <View style={styles.alertIconContainer}>
              <Ionicons name="alert-circle" size={40} color="#ff4444"/>
            </View>
            <Text style={styles.alertTitle}>GuardIt Security Alert</Text>
            <Text style={styles.alertSubtitle}>System Status: Active & Monitoring</Text>
            <View style={styles.alertStatusRow}>
              <View style={styles.statusIndicator}>
                <View style={styles.statusDot} />
                <Text style={styles.statusText}>Live</Text>
              </View>
              <View style={styles.statusIndicator}>
                <View style={styles.statusDot} />
                <Text style={styles.statusText}>Protected</Text>
              </View>
              <View style={styles.statusIndicator}>
                <View style={styles.statusDot} />
                <Text style={styles.statusText}>24/7</Text>
              </View>
            </View>
          </LinearGradient>
        </View>

        {notification && (
          <View style={styles.notificationContainer}>
            <Text style={styles.notificationTitle}>Latest Security Alert</Text>
            <LinearGradient
              colors={['rgba(255, 68, 68, 0.25)', 'rgba(255, 68, 68, 0.15)']}
              style={styles.notificationBox}
            >
              <View style={styles.notificationIcon}>
                <Ionicons name="warning" size={28} color="#ff4444"/>
              </View>
              <View style={styles.notificationContent}>
                <Text style={styles.notificationText}>{notification.request.content.title}</Text>
                <Text style={styles.notificationBody}>{notification.request.content.body}</Text>
                <Text style={styles.notificationTime}>Just now</Text>
              </View>
            </LinearGradient>
          </View>
        )}

        <View style={styles.statusContainer}>
          <View style={styles.statusCard}>
            <LinearGradient
              colors={['rgba(255, 68,68, 0.15)', 'rgba(255, 68,68, 0.25)']}
              style={styles.cardGradient}
            >
              <View style={styles.cardIconContainer}>
                <Ionicons name="videocam" size={36} color="#ff4444"/>
              </View>
              <Text style={styles.cardTitle}>Live Video</Text>
              <Text style={styles.cardSubtitle}>Enter camera server IP</Text>
              
              <View style={styles.ipInputContainer}>
                <TextInput
                  style={styles.ipInput}
                  value={cameraIP}
                  onChangeText={setCameraIP}
                  placeholder="192.168.1.100:8090"
                  placeholderTextColor="rgba(255, 255, 255, 0.5)"
                  keyboardType="url"
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>
              
              <TouchableOpacity style={styles.cardButton} onPress={openCameraStream}>
                <Text style={styles.cardButtonText}>VIEW STREAM</Text>
              </TouchableOpacity>
            </LinearGradient>
          </View>

          <View style={styles.statusCard}>
            <LinearGradient
              colors={['rgba(255, 68,68, 0.15)', 'rgba(255, 68,68, 0.25)']}
              style={styles.cardGradient}
            >
              <View style={styles.cardIconContainer}>
                <Ionicons name="notifications" size={36} color="#ff4444"/>
                {unreadCount > 0 && (
                  <View style={styles.unreadBadge}>
                    <Text style={styles.unreadBadgeText}>{unreadCount}</Text>
                  </View>
                )}
              </View>
              <Text style={styles.cardTitle}>Notifications</Text>
              <Text style={styles.cardSubtitle}>
                {unreadCount > 0 ? `${unreadCount} unread alert${unreadCount !== 1 ? 's' : ''}` : 'Alert system ready'}
              </Text>
              <TouchableOpacity style={styles.cardButton} onPress={() => navigation.navigate('Notifications')}>
                <Text style={styles.cardButtonText}>SEE NOTIFICATIONS</Text>
              </TouchableOpacity>
            </LinearGradient>
          </View>

          <View style={styles.statusCard}>
            <LinearGradient
              colors={['rgba(255, 68,68, 0.15)', 'rgba(255, 68,68, 0.25)']}
              style={styles.cardGradient}
            >
              <View style={styles.cardIconContainer}>
                <Ionicons name="speedometer" size={36} color="#ff4444"/>
              </View>
              <Text style={styles.cardTitle}>Raspberry Pi Connection</Text>
              <Text style={styles.cardSubtitle}>Raspberry Pi motion detection</Text>
              <TouchableOpacity style={styles.cardButton} onPress={() => navigation.navigate('IMU')}>
                <Text style={styles.cardButtonText}>CONNECT RASPBERRY PI</Text>
              </TouchableOpacity>
            </LinearGradient>
          </View>
        </View>

        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <LinearGradient
            colors={['#ff4444', '#ff6666']}
            style={styles.logoutGradient}
          >
            <Ionicons name="log-out-outline" size={20} color="white"/>
            <Text style={styles.logoutText}>SECURE LOGOUT</Text>
          </LinearGradient>
        </TouchableOpacity>
      </ScrollView>

      <View style={styles.footer}>
        <Text style={styles.footerText}>24/7 Security Monitoring Active</Text>
        <View style={styles.securityIcons}>
          <Ionicons name="shield" size={16} color="#ff4444"/>
          <Ionicons name="lock-closed" size={16} color="#ff4444"/>
          <Ionicons name="eye" size={16} color="#ff4444"/>
        </View>
      </View>
    </LinearGradient>
  );
}

async function registerForPushNotificationsAsync() {
  let token;
  if (Device.isDevice) {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    if (finalStatus !== 'granted') {
      return '';
    }
    token = (await Notifications.getExpoPushTokenAsync()).data;
  } else {
    return '';
  }

  if (Platform.OS === 'android') {
    Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF231F7C',
    });
  }

  return token;
}

const styles = StyleSheet.create({
  container: {
    flex: 1
  },
  header: {
    alignItems: 'center',
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingBottom: 30,
    paddingHorizontal: 20,
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
    paddingHorizontal: 20,
  },
  logoBackground: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 68, 68, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 68, 68, 0.3)',
    shadowColor: '#ff4444',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  logoTextContainer: {
    marginLeft: 20,
    alignItems: 'flex-start',
  },
  logoText: {
    fontSize: 36,
    fontWeight: 'bold',
    color: 'white',
    letterSpacing: 2,
    textShadowColor: 'rgba(255, 68, 68, 0.5)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  subtitle: {
    fontSize: 12,
    color: '#ff4444',
    fontWeight: '700',
    letterSpacing: 4,
    marginTop: 4,
    textShadowColor: 'rgba(255, 68, 68, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
  },
  welcomeContainer: {
    alignItems: 'center',
    marginBottom: 40,
    paddingTop: 10,
  },
  welcomeTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 12,
    textAlign: 'center',
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: '#ccc',
    textAlign: 'center',
    lineHeight: 22,
  },
  statusContainer: {
    marginBottom: 40,
  },
  statusCard: {
    marginBottom: 20,
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 68,68, 0.2)',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  cardGradient: {
    padding: 24,
    alignItems: 'center',
  },
  cardIconContainer: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: 'rgba(255, 68, 68, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 68, 68, 0.3)',
    position: 'relative',
  },
  unreadBadge: {
    position: 'absolute',
    top: -5,
    right: -5,
    backgroundColor: '#ff4444',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#0a0a0a',
  },
  unreadBadgeText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
    textAlign: 'center',
  },
  cardSubtitle: {
    fontSize: 14,
    color: '#ccc',
    marginBottom: 15,
    textAlign: 'center',
    lineHeight: 20,
  },
  ipInputContainer: {
    marginBottom: 15,
    width: '100%',
  },
  ipInput: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 8,
    paddingHorizontal: 15,
    paddingVertical: 10,
    fontSize: 14,
    color: 'white',
    textAlign: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  cardButton: {
    backgroundColor: 'rgba(255, 68,68, 0.2)',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 68,68, 0.3)',
    minWidth: 120,
    alignItems: 'center',
  },
  cardButtonText: {
    color: '#ff4444',
    fontSize: 13,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  notificationContainer: {
    marginBottom: 30,
  },
  notificationTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 16,
    textAlign: 'center',
  },
  notificationBox: {
    backgroundColor: 'rgba(255, 68,68, 0.1)',
    borderRadius: 16,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'flex-start',
    borderWidth: 1,
    borderColor: 'rgba(255, 68,68, 0.2)',
  },
  notificationIcon: {
    marginRight: 16,
    marginTop: 2,
  },
  notificationContent: {
    flex: 1,
  },
  notificationText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 6,
  },
  notificationBody: {
    fontSize: 14,
    color: '#ccc',
    lineHeight: 20,
  },
  notificationTime: {
    fontSize: 12,
    color: '#999',
    marginTop: 8,
    fontStyle: 'italic',
  },
  alertSection: {
    marginBottom: 40,
  },
  alertContainer: {
    padding: 24,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 68, 68, 0.2)',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  alertIconContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  alertTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
    textAlign: 'center',
  },
  alertSubtitle: {
    fontSize: 14,
    color: '#ccc',
    marginBottom: 20,
    textAlign: 'center',
  },
  alertStatusRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 10,
  },
  statusIndicator: {
    alignItems: 'center',
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#ff4444',
    marginBottom: 4,
  },
  statusText: {
    fontSize: 12,
    color: '#ccc',
  },
  logoutButton: {
    marginBottom: 40,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  logoutGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
  },
  logoutText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
    letterSpacing: 1,
  },
  footer: {
    alignItems: 'center',
    paddingBottom: Platform.OS === 'ios' ? 40 : 30,
    paddingTop: 20,
  },
  footerText: {
    color: '#666',
    fontSize: 13,
    marginBottom: 12,
    fontWeight: '500',
  },
  securityIcons: {
    flexDirection: 'row',
    gap: 20,
  },
});

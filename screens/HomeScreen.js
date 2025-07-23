import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform, ScrollView, Alert, Dimensions, Linking, TextInput, Image } from 'react-native';
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
      <View style={styles.centeredContent}>
        {/* Logo with glow */}
        <View style={styles.logoGlowWrapper}>
          <Image 
            source={require('../assets/guardit.png')} 
            style={styles.logoImage}
            resizeMode="contain"
          />
          </View>
          <View style={styles.logoTextContainer}>
            <Text style={styles.logoText}>GuardIt</Text>
            <Text style={styles.subtitle}>SECURITY SYSTEM</Text>
      </View>

        {/* Welcome Card */}
        <View style={styles.welcomeCard}>
          <Text style={styles.welcomeTitle}>Welcome Back!</Text>
          <Text style={styles.welcomeSubtitle}>Your security system is active and monitoring</Text>
        </View>

        {/* Connect Devices Button */}
        <TouchableOpacity
          style={({ pressed }) => [styles.connectButton, { marginTop: 24 }, pressed && styles.connectButtonPressed]}
          onPress={() => navigation.navigate('Connection')}
          activeOpacity={0.85}
        >
          <LinearGradient
            colors={['#ff4444', '#ff6666']}
            style={styles.connectButtonGradient}
          >
            <Ionicons name="wifi" size={20} color="white" style={{ marginRight: 8 }} />
            <Text style={styles.connectButtonText}>Connect Devices</Text>
          </LinearGradient>
        </TouchableOpacity>

        {/* Secure Logout Button (now absolutely positioned) */}
        <View style={styles.logoutButtonWrapper} pointerEvents="box-none">
          <TouchableOpacity
            style={({ pressed }) => [styles.logoutButton, pressed && styles.logoutButtonPressed]}
            onPress={handleLogout}
            activeOpacity={0.85}
          >
            <LinearGradient
              colors={['#ff4444', '#ff6666']}
              style={styles.logoutGradient}
            >
              <Text style={styles.logoutText}>SECURE LOGOUT</Text>
            </LinearGradient>
              </TouchableOpacity>
        </View>
      </View>
      {/* Footer with fade */}
          <LinearGradient
        colors={['transparent', 'rgba(0,0,0,0.5)']}
        style={styles.footerFade}
        pointerEvents="none"
      >
      <View style={styles.footer}>
        <Text style={styles.footerText}>24/7 Security Monitoring Active</Text>
        </View>
      </LinearGradient>
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
  centeredContent: {
    flex: 1,
    justifyContent: 'flex-start',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: 70,
  },
  logoGlowWrapper: {
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 0,
  },
  logoGlow: {
    position: 'absolute',
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: 'rgba(255, 68, 68, 0.25)',
    shadowColor: '#ff4444',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.7,
    shadowRadius: 30,
  },
  logoCircle: {
    width: 90,
    height: 90,
    borderRadius: 45,
    borderWidth: 3,
    borderColor: '#ff4444',
    backgroundColor: 'rgba(255, 68, 68, 0.08)',
  },
  logoTextContainer: {
    alignItems: 'center',
    marginBottom: 0,
  },
  logoText: {
    fontSize: 38,
    fontWeight: 'bold',
    color: 'white',
    letterSpacing: 1,
    textShadowColor: 'rgba(255, 68, 68, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 6,
  },
  subtitle: {
    fontSize: 16,
    color: '#ff4444',
    fontWeight: 'bold',
    letterSpacing: 2,
    marginTop: 2,
    textShadowColor: 'rgba(255, 68, 68, 0.15)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  welcomeCard: {
    backgroundColor: 'rgba(255,255,255,0.07)',
    borderRadius: 18,
    paddingVertical: 28,
    paddingHorizontal: 32,
    alignItems: 'center',
    marginBottom: 56,
    marginTop: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
  },
  welcomeTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 10,
    textShadowColor: 'rgba(255, 68, 68, 0.25)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 6,
  },
  welcomeSubtitle: {
    fontSize: 17,
    color: 'rgba(255,255,255,0.75)',
    textAlign: 'center',
    lineHeight: 24,
  },
  connectButton: {
    borderRadius: 40,
    overflow: 'hidden',
    backgroundColor: '#1a1a1a',
    borderWidth: 1.5,
    borderColor: 'rgba(255,255,255,0.12)',
    width: 260,
    alignSelf: 'center',
    marginTop: "80",
    marginBottom: 40,
    shadowColor: '#ff4444',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.13,
    shadowRadius: 12,
  },
  connectButtonPressed: {
    borderColor: '#fff',
    shadowColor: '#fff',
    shadowOpacity: 0.18,
    opacity: 0.93,
    transform: [{ scale: 0.97 }],
  },
  connectButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 22,
    borderRadius: 40,
  },
  connectButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
    letterSpacing: 0.5,
  },
  connectSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  connectArrow: {
    marginLeft: 'auto',
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
  logoutButtonWrapper: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 90,
    alignItems: 'center',
    zIndex: 10,
    pointerEvents: 'box-none',
    marginTop: 40,
  },
  logoutButton: {
    borderRadius: 40,
    overflow: 'hidden',
    width: '92%',
    minWidth: 260,
    maxWidth: 400,
    alignSelf: 'center',
    marginBottom: 0,
    shadowColor: '#ff4444',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.13,
    shadowRadius: 12,
    borderWidth: 1.5,
    borderColor: 'rgba(255,255,255,0.12)',
  },
  logoutButtonPressed: {
    shadowColor: '#fff',
    shadowOpacity: 0.18,
    opacity: 0.93,
    transform: [{ scale: 0.98 }],
  },
  logoutGradient: {
    paddingVertical: 16,
    paddingHorizontal: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 40,
  },
  logoutText: {
    color: 'white',
    fontSize: 15,
    fontWeight: '600',
    letterSpacing: 1,
  },
  footerFade: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: 90,
    justifyContent: 'flex-end',
  },
  footer: {
    alignItems: 'center',
    marginBottom: 18,
  },
  footerText: {
    color: 'rgba(255,255,255,0.35)',
    fontSize: 13,
    letterSpacing: 0.5,
  },
  securityIcons: {
    flexDirection: 'row',
    gap: 20,
  },
  logoCircleShadow: {
    shadowColor: '#ff4444',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    borderRadius: 60,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoCircle: {
    width: 90,
    height: 90,
    borderRadius: 45,
    borderWidth: 3,
    borderColor: '#ff4444',
    backgroundColor: 'rgba(255, 68, 68, 0.08)',
  },
  logoImage: {
    width: 180,
    height: 180,
    borderRadius: 90,
  },
});

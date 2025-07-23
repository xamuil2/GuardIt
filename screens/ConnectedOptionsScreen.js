import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation, useRoute } from '@react-navigation/native';

export default function ConnectedOptionsScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { raspberryPiIP, cameraStreamIP } = route.params || {};

  const openCameraStream = () => {
    navigation.navigate('CameraStream', { cameraIP: cameraStreamIP });
  };

  const openNotifications = () => {
    navigation.navigate('Notifications');
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
          <Text style={styles.headerTitle}>Connected!</Text>
          <Text style={styles.headerSubtitle}>Choose what you'd like to do</Text>
        </View>
        <View style={styles.headerSpacer} />
      </View>

      <View style={styles.content}>
        <View style={styles.optionsContainer}>
          <TouchableOpacity style={styles.optionCard} onPress={openCameraStream}>
            <LinearGradient
              colors={['rgba(255, 68, 68, 0.15)', 'rgba(255, 68, 68, 0.05)']}
              style={styles.optionCardGradient}
            >
              <View style={styles.optionIconContainer}>
                <Ionicons name="videocam" size={48} color="#ff4444"/>
              </View>
              <Text style={styles.optionTitle}>Camera Stream</Text>
              <Text style={styles.optionSubtitle}>View live security feed</Text>
              <View style={styles.optionArrow}>
                <Ionicons name="arrow-forward" size={24} color="#ff4444"/>
              </View>
            </LinearGradient>
          </TouchableOpacity>

          <TouchableOpacity style={styles.optionCard} onPress={openNotifications}>
            <LinearGradient
              colors={['rgba(255, 68, 68, 0.15)', 'rgba(255, 68, 68, 0.05)']}
              style={styles.optionCardGradient}
            >
              <View style={styles.optionIconContainer}>
                <Ionicons name="notifications" size={48} color="#ff4444"/>
              </View>
              <Text style={styles.optionTitle}>Notifications</Text>
              <Text style={styles.optionSubtitle}>View security alerts</Text>
              <View style={styles.optionArrow}>
                <Ionicons name="arrow-forward" size={24} color="#ff4444"/>
              </View>
            </LinearGradient>
          </TouchableOpacity>
        </View>

        <View style={styles.connectionInfo}>
          <LinearGradient
            colors={['rgba(68, 255, 68, 0.1)', 'rgba(68, 255, 68, 0.05)']}
            style={styles.connectionInfoGradient}
          >
            <View style={styles.connectionInfoHeader}>
              <Ionicons name="wifi" size={20} color="#44ff44"/>
              <Text style={styles.connectionInfoTitle}>Connected Devices</Text>
            </View>
            <View style={styles.connectionInfoRow}>
              <Text style={styles.connectionInfoLabel}>Raspberry Pi:</Text>
              <Text style={styles.connectionInfoValue}>{raspberryPiIP}</Text>
            </View>
            <View style={styles.connectionInfoRow}>
              <Text style={styles.connectionInfoLabel}>Camera Stream:</Text>
              <Text style={styles.connectionInfoValue}>{cameraStreamIP}</Text>
            </View>
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
  optionsContainer: {
    gap: 20,
    marginBottom: 30,
  },
  optionCard: {
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: 'rgba(255, 68, 68, 0.15)',
    shadowColor: '#ff4444',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
  },
  optionCardGradient: {
    padding: 25,
    backgroundColor: 'transparent',
    flexDirection: 'row',
    alignItems: 'center',
  },
  optionIconContainer: {
    marginRight: 20,
  },
  optionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 5,
  },
  optionSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  optionArrow: {
    marginLeft: 'auto',
  },
  connectionInfo: {
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: 'rgba(68, 255, 68, 0.15)',
  },
  connectionInfoGradient: {
    padding: 20,
    backgroundColor: 'transparent',
  },
  connectionInfoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  connectionInfoTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
    marginLeft: 10,
  },
  connectionInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  connectionInfoLabel: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  connectionInfoValue: {
    fontSize: 14,
    color: '#44ff44',
    fontWeight: '600',
  },
}); 
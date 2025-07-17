import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../context/AuthContext';
import { useDevice } from '../context/DeviceContext';

const SettingsScreen: React.FC = () => {
  const { user, logout } = useAuth();
  const { deviceStatus, disconnectDevice } = useDevice();

  const handleLogout = async () => {
    Alert.alert('Logout', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Logout', style: 'destructive', onPress: logout },
    ]);
  };

  return (
    <LinearGradient colors={['#6366f1', '#8b5cf6']} style={styles.container}>
      <Text style={styles.title}>Settings</Text>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Account</Text>
        <View style={styles.row}>
          <Ionicons name="person-circle" size={28} color="#6366f1" />
          <Text style={styles.infoText}>{user?.name || 'Unknown User'}</Text>
        </View>
        <View style={styles.row}>
          <Ionicons name="mail" size={24} color="#6366f1" />
          <Text style={styles.infoText}>{user?.email || 'No Email'}</Text>
        </View>
      </View>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Device</Text>
        <View style={styles.row}>
          <Ionicons name={deviceStatus.isConnected ? 'wifi' : 'close-circle'} size={24} color={deviceStatus.isConnected ? '#22c55e' : '#ef4444'} />
          <Text style={styles.infoText}>{deviceStatus.isConnected ? 'Connected' : 'Disconnected'}</Text>
        </View>
        <View style={styles.row}>
          <Ionicons name="battery-half" size={24} color="#6366f1" />
          <Text style={styles.infoText}>Battery: {deviceStatus.batteryLevel}%</Text>
        </View>
        <TouchableOpacity style={styles.disconnectButton} onPress={disconnectDevice}>
          <Ionicons name="close-circle" size={20} color="#ef4444" />
          <Text style={styles.disconnectText}>Disconnect Device</Text>
        </TouchableOpacity>
      </View>
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Ionicons name="log-out-outline" size={22} color="white" />
        <Text style={styles.logoutText}>Log Out</Text>
      </TouchableOpacity>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 60,
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 26,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 30,
    alignSelf: 'center',
  },
  section: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6366f1',
    marginBottom: 10,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  infoText: {
    marginLeft: 12,
    fontSize: 16,
    color: '#374151',
  },
  disconnectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
    backgroundColor: '#fee2e2',
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 14,
    alignSelf: 'flex-start',
  },
  disconnectText: {
    color: '#ef4444',
    fontWeight: '600',
    marginLeft: 6,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#6366f1',
    borderRadius: 12,
    paddingVertical: 16,
    marginTop: 30,
  },
  logoutText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
    marginLeft: 10,
  },
});

export default SettingsScreen; 
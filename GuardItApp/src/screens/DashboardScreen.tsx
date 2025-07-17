import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const DashboardScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Ionicons name="shield-checkmark" size={40} color="#6366f1" style={styles.icon} />
        <Text style={styles.title}>GuardIt Dashboard</Text>
      </View>

      {/* Device Status */}
      <View style={styles.statusCard}>
        <Text style={styles.statusTitle}>Device Status</Text>
        <View style={styles.statusRow}>
          <Ionicons name="wifi" size={24} color="#10b981" />
          <Text style={styles.statusText}>Connected</Text>
        </View>
        <View style={styles.statusRow}>
          <Ionicons name="battery-half" size={24} color="#f59e42" />
          <Text style={styles.statusText}>Battery: 85%</Text>
        </View>
        <View style={styles.statusRow}>
          <Ionicons name="time" size={24} color="#6366f1" />
          <Text style={styles.statusText}>Last Seen: 2 min ago</Text>
        </View>
      </View>

      {/* Video Feed */}
      <TouchableOpacity 
        style={styles.videoCard}
        onPress={() => navigation.navigate('Camera')}
      >
        <View style={styles.videoHeader}>
          <Ionicons name="videocam" size={24} color="#6366f1" />
          <Text style={styles.videoTitle}>Live Camera Feed</Text>
        </View>
        <View style={styles.videoPlaceholder}>
          <Ionicons name="play-circle" size={48} color="#6366f1" />
          <Text style={styles.videoText}>Tap to view live feed</Text>
        </View>
      </TouchableOpacity>

      {/* Action Button */}
      <TouchableOpacity style={styles.button}>
        <Ionicons name="alert-circle" size={20} color="#fff" />
        <Text style={styles.buttonText}>Ring Alarm</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
    alignItems: 'center',
    paddingTop: 60,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 30,
  },
  icon: {
    marginRight: 12,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#22223b',
  },
  statusCard: {
    width: '90%',
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 3,
  },
  statusTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
    color: '#6366f1',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  statusText: {
    marginLeft: 10,
    fontSize: 16,
    color: '#22223b',
  },
  videoCard: {
    width: '90%',
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 3,
  },
  videoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  videoTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginLeft: 8,
    color: '#6366f1',
  },
  videoPlaceholder: {
    height: 120,
    backgroundColor: '#f8fafc',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#e2e8f0',
    borderStyle: 'dashed',
  },
  videoText: {
    marginTop: 8,
    fontSize: 14,
    color: '#64748b',
    fontWeight: '500',
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#6366f1',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 12,
    shadowColor: '#6366f1',
    shadowOpacity: 0.2,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
});

export default DashboardScreen; 
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

export default function MapScreen({ navigation }) {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton} 
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Device Location</Text>
        <View style={styles.placeholder} />
      </View>

      <View style={styles.mapContainer}>
        <View style={styles.mapPlaceholder}>
          <Text style={styles.mapIcon}>🗺️</Text>
          <Text style={styles.mapTitle}>GPS Map</Text>
          <Text style={styles.mapSubtitle}>Location tracking will be available when you connect your hardware device</Text>
        </View>
      </View>

      <View style={styles.statusContainer}>
        <View style={styles.statusCard}>
          <Text style={styles.statusTitle}>Location Tracking</Text>
          <Text style={styles.statusText}>Ready for hardware integration</Text>
          <Text style={styles.statusSubtext}>Device location will be displayed here</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 60,
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  backButton: {
    padding: 8,
  },
  backText: {
    color: 'white',
    fontSize: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
  },
  placeholder: {
    width: 40,
  },
  mapContainer: {
    flex: 1,
    marginHorizontal: 20,
    marginBottom: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#ff4444',
    backgroundColor: 'rgba(255,255,255,0.05)',
  },
  mapPlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  mapIcon: {
    fontSize: 64,
  },
  mapTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginTop: 16,
    marginBottom: 8,
  },
  mapSubtitle: {
    fontSize: 14,
    color: '#ccc',
    textAlign: 'center',
    lineHeight: 20,
  },
  statusContainer: {
    paddingHorizontal: 20,
    paddingBottom: 30,
  },
  statusCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#ff4444',
    backgroundColor: 'rgba(255, 68, 68, 0.1)',
  },
  statusTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
  },
  statusText: {
    fontSize: 14,
    color: '#ccc',
    marginBottom: 4,
  },
  statusSubtext: {
    fontSize: 12,
    color: '#ff4444',
    fontWeight: '600',
  },
}); 
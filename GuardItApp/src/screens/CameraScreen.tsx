import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

const CameraScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const [loading, setLoading] = useState(false);
  const [feedKey, setFeedKey] = useState(0);

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => {
      setFeedKey(prev => prev + 1);
      setLoading(false);
    }, 1200);
  };

  return (
    <LinearGradient colors={['#6366f1', '#8b5cf6']} style={styles.container}>
      <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
        <Ionicons name="arrow-back" size={28} color="white" />
      </TouchableOpacity>
      <Text style={styles.title}>Live Camera Feed</Text>
      <View style={styles.feedContainer}>
        {loading ? (
          <ActivityIndicator size="large" color="#6366f1" />
        ) : (
          <Image
            key={feedKey}
            source={{ uri: 'https://placekitten.com/400/250' }}
            style={styles.cameraImage}
            resizeMode="cover"
          />
        )}
      </View>
      <TouchableOpacity style={styles.refreshButton} onPress={handleRefresh}>
        <Ionicons name="refresh" size={22} color="white" />
        <Text style={styles.refreshText}>Refresh Feed</Text>
      </TouchableOpacity>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 60,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  backButton: {
    position: 'absolute',
    top: 50,
    left: 20,
    zIndex: 2,
    backgroundColor: 'rgba(0,0,0,0.15)',
    borderRadius: 20,
    padding: 6,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 20,
    marginTop: 10,
  },
  feedContainer: {
    width: '100%',
    height: 250,
    backgroundColor: '#e5e7eb',
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 30,
    overflow: 'hidden',
  },
  cameraImage: {
    width: '100%',
    height: '100%',
  },
  refreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#6366f1',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 24,
    marginTop: 10,
  },
  refreshText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
    marginLeft: 10,
  },
});

export default CameraScreen; 
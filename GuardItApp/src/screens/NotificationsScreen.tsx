import React from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

const mockNotifications = [
  { id: '1', type: 'motion', message: 'Motion detected near your backpack', time: '2 min ago' },
  { id: '2', type: 'suspicious', message: 'Suspicious activity detected!', time: '10 min ago' },
  { id: '3', type: 'battery', message: 'Battery low: 20%', time: '1 hour ago' },
  { id: '4', type: 'connected', message: 'Device connected', time: '2 hours ago' },
];

const iconMap: Record<string, { name: any; color: string }> = {
  motion: { name: 'walk', color: '#6366f1' },
  suspicious: { name: 'alert-circle', color: '#f59e42' },
  battery: { name: 'battery-dead', color: '#ef4444' },
  connected: { name: 'wifi', color: '#22c55e' },
};

const NotificationsScreen: React.FC = () => {
  return (
    <LinearGradient colors={['#6366f1', '#8b5cf6']} style={styles.container}>
      <Text style={styles.title}>Notifications</Text>
      <FlatList
        data={mockNotifications}
        keyExtractor={item => item.id}
        renderItem={({ item }) => {
          const icon = iconMap[item.type] || { name: 'notifications', color: '#6366f1' };
          return (
            <View style={styles.notificationCard}>
              <Ionicons name={icon.name} size={28} color={icon.color} style={styles.icon} />
              <View style={styles.textContainer}>
                <Text style={styles.message}>{item.message}</Text>
                <Text style={styles.time}>{item.time}</Text>
              </View>
            </View>
          );
        }}
        contentContainerStyle={{ paddingBottom: 30 }}
        showsVerticalScrollIndicator={false}
      />
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
  notificationCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 18,
    marginBottom: 18,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  icon: {
    marginRight: 16,
  },
  textContainer: {
    flex: 1,
  },
  message: {
    fontSize: 16,
    color: '#374151',
    fontWeight: '500',
    marginBottom: 4,
  },
  time: {
    fontSize: 13,
    color: '#9ca3af',
  },
});

export default NotificationsScreen; 
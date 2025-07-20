import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform, ScrollView, Alert, Dimensions, FlatList } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import NotificationService from '../services/NotificationService';
const { width, height } = Dimensions.get('window');

export default function NotificationsScreen() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const navigation = useNavigation();

  useFocusEffect(
    React.useCallback(() => {
      loadNotifications();
    }, [])
  );

  const loadNotifications = () => {
    const allNotifications = NotificationService.getNotifications();
    const unread = NotificationService.getUnreadCount();
    setNotifications(allNotifications);
    setUnreadCount(unread);
  };

  const markAsRead = async (notificationId) => {
    await NotificationService.markAsRead(notificationId);
    loadNotifications();
  };

  const markAllAsRead = async () => {
    Alert.alert(
      'Mark All as Read',
      'Are you sure you want to mark all notifications as read?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Mark All Read',
          onPress: async () => {
            await NotificationService.markAllAsRead();
            loadNotifications();
          }
        }
      ]
    );
  };

  const clearAllNotifications = async () => {
    Alert.alert(
      'Clear All Notifications',
      'Are you sure you want to delete all notifications? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear All',
          style: 'destructive',
          onPress: async () => {
            await NotificationService.clearAllNotifications();
            loadNotifications();
          }
        }
      ]
    );
  };

  const deleteNotification = async (notificationId) => {
    Alert.alert(
      'Delete Notification',
      'Are you sure you want to delete this notification?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            await NotificationService.deleteNotification(notificationId);
            loadNotifications();
          }
        }
      ]
    );
  };

  const renderNotification = ({ item }) => (
    <TouchableOpacity
      style={[styles.notificationItem, !item.read && styles.unreadNotification]}
      onPress={() => markAsRead(item.id)}
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
              name={item.type === 'led_alert' ? 'warning' : 'notifications'} 
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
              <Text style={[styles.notificationDate, item.read && styles.readText]}>
                {item.date} at {item.time}
              </Text>
            </View>
          </View>
          <TouchableOpacity
            style={styles.deleteButton}
            onPress={() => deleteNotification(item.id)}
          >
            <Ionicons name="trash-outline" size={20} color="#888" />
          </TouchableOpacity>
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyContainer}>
      <LinearGradient
        colors={['rgba(255, 255, 255, 0.05)', 'rgba(255, 255, 255, 0.02)']}
        style={styles.emptyGradient}
      >
        <Ionicons name="notifications-off" size={64} color="#888" />
        <Text style={styles.emptyTitle}>No Notifications</Text>
        <Text style={styles.emptySubtitle}>
          You'll see alerts here when your GuardIt device detects movement or other security events.
        </Text>
      </LinearGradient>
    </View>
  );

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
        <Text style={styles.headerTitle}>Notifications</Text>
        <View style={styles.headerActions}>
          {unreadCount > 0 && (
            <TouchableOpacity style={styles.markAllButton} onPress={markAllAsRead}>
              <Ionicons name="checkmark-done" size={20} color="#44ff44"/>
            </TouchableOpacity>
          )}
          {notifications.length > 0 && (
            <TouchableOpacity style={styles.clearAllButton} onPress={clearAllNotifications}>
              <Ionicons name="trash" size={20} color="#ff4444"/>
            </TouchableOpacity>
          )}
        </View>
      </View>

      <View style={styles.content}>
        {unreadCount > 0 && (
          <View style={styles.unreadBanner}>
            <LinearGradient
              colors={['rgba(255, 68, 68, 0.2)', 'rgba(255, 68, 68, 0.1)']}
              style={styles.unreadBannerGradient}
            >
              <Ionicons name="notifications" size={20} color="#ff4444"/>
              <Text style={styles.unreadText}>
                {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
              </Text>
              <TouchableOpacity onPress={markAllAsRead}>
                <Text style={styles.markAllText}>Mark all read</Text>
              </TouchableOpacity>
            </LinearGradient>
          </View>
        )}

        {notifications.length === 0 ? (
          renderEmptyState()
        ) : (
          <FlatList
            data={notifications}
            renderItem={renderNotification}
            keyExtractor={(item) => item.id}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.notificationsList}
          />
        )}
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1
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
  headerActions: {
    flexDirection: 'row',
    gap: 10,
  },
  markAllButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(68, 255, 68, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  clearAllButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 68, 68, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  unreadBanner: {
    marginBottom: 20,
  },
  unreadBannerGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderRadius: 15,
  },
  unreadText: {
    flex: 1,
    color: '#ff4444',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  markAllText: {
    color: '#44ff44',
    fontSize: 14,
    fontWeight: 'bold',
  },
  notificationsList: {
    paddingBottom: 20,
  },
  notificationItem: {
    marginBottom: 15,
    borderRadius: 15,
    overflow: 'hidden',
  },
  unreadNotification: {
    borderWidth: 1,
    borderColor: 'rgba(255, 68, 68, 0.3)',
  },
  notificationGradient: {
    padding: 20,
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
  },
  notificationBody: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
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
    color: 'rgba(255, 255, 255, 0.6)',
  },
  notificationDate: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  readText: {
    color: 'rgba(255, 255, 255, 0.5)',
  },
  deleteButton: {
    padding: 5,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyGradient: {
    alignItems: 'center',
    padding: 40,
    borderRadius: 20,
    width: '100%',
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginTop: 20,
    marginBottom: 10,
  },
  emptySubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    lineHeight: 24,
  },
}); 
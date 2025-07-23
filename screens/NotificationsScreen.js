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
  const [notificationService] = useState(NotificationService);
  const navigation = useNavigation();

  useFocusEffect(
    React.useCallback(() => {
      loadNotifications();
    }, [notificationService])
  );

  const loadNotifications = () => {
    const allNotifications = notificationService.getNotifications();
    const unread = notificationService.getUnreadCount();
    setNotifications(allNotifications);
    setUnreadCount(unread);
  };

  const markAsRead = async (notificationId) => {
    await notificationService.markAsRead(notificationId);
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
            await notificationService.markAllAsRead();
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
            await notificationService.clearAllNotifications();
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
            await notificationService.deleteNotification(notificationId);
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
                {notificationService.formatTimestamp(item.timestamp)}
              </Text>
              <Text style={[styles.notificationDate, item.read && styles.readText]}>
                {item.date} {item.time}
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
        colors={['rgba(255, 68, 68, 0.1)', 'rgba(255, 68, 68, 0.05)']}
        style={styles.emptyGradient}
      >
        <View style={styles.emptyIconContainer}>
          <LinearGradient
            colors={['rgba(255, 68, 68, 0.2)', 'rgba(255, 68, 68, 0.1)']}
            style={styles.emptyIconBackground}
          >
            <Ionicons name="arrow-back" size={48} color="white" />
          </LinearGradient>
        </View>
        <Text style={styles.emptyTitle}>No Notifications</Text>
        <Text style={styles.emptySubtitle}>
          You'll see alerts here when your GuardIt device detects movement or other security events.
        </Text>
        <View style={styles.emptyDivider} />
        <Text style={styles.emptyHint}>
          Your security system is monitoring and will notify you of any activity
        </Text>
      </LinearGradient>
    </View>
  );

  return (
    <LinearGradient
      colors={['#0a0a0a', '#1a1a1a', '#0a0a0a']}
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
          <Text style={styles.headerTitle}>Notifications</Text>
          <Text style={styles.headerSubtitle}>Security Alerts & Updates</Text>
        </View>
        <View style={styles.headerActions}>
          {unreadCount > 0 && (
            <TouchableOpacity style={styles.markAllButton} onPress={markAllAsRead}>
              <LinearGradient
                colors={['rgba(68, 255, 68, 0.2)', 'rgba(68, 255, 68, 0.1)']}
                style={styles.actionButtonGradient}
              >
                <Ionicons name="checkmark-done" size={18} color="#44ff44"/>
              </LinearGradient>
            </TouchableOpacity>
          )}
          {notifications.length > 0 && (
            <TouchableOpacity style={styles.clearAllButton} onPress={clearAllNotifications}>
              <LinearGradient
                colors={['rgba(255, 68, 68, 0.2)', 'rgba(255, 68, 68, 0.1)']}
                style={styles.actionButtonGradient}
              >
                <Ionicons name="trash" size={18} color="#ff4444"/>
              </LinearGradient>
            </TouchableOpacity>
          )}
        </View>
      </View>

      <View style={styles.content}>
        {unreadCount > 0 && (
          <View style={styles.unreadBanner}>
            <LinearGradient
              colors={['rgba(255, 68, 68, 0.15)', 'rgba(255, 68, 68, 0.08)']}
              style={styles.unreadBannerGradient}
            >
              <View style={styles.unreadIconContainer}>
                <Ionicons name="notifications" size={20} color="#ff4444"/>
              </View>
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
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingBottom: 20,
    paddingHorizontal: 20,
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
    borderWidth: 1,
    borderColor: 'rgba(68, 255, 68, 0.3)',
  },
  clearAllButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 68, 68, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 68, 68, 0.3)',
  },
  headerContent: {
    flex: 1,
  },
  backButtonGradient: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ff4444',
  },
  actionButtonGradient: {
    width: 40,
    height: 40,
    borderRadius: 20,
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
    backgroundColor: 'rgba(255, 68, 68, 0.15)',
    borderWidth: 1,
    borderColor: '#ff4444',
  },
  unreadIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 68, 68, 0.2)',
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
    padding: 20,
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
  notificationDate: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
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
    backgroundColor: '#0a0a0a',
  },
  emptyGradient: {
    alignItems: 'center',
    padding: 40,
    borderRadius: 20,
    width: '100%',
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#ff4444',
  },
  emptyIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  emptyIconBackground: {
    width: '100%',
    height: '100%',
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ff4444',
    marginTop: 20,
    marginBottom: 10,
    textShadowColor: 'rgba(255, 68, 68, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  emptySubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 20,
  },
  emptyDivider: {
    width: '80%',
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    marginBottom: 15,
  },
  emptyHint: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    lineHeight: 20,
  },
});

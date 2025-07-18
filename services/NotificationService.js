import * as Notifications from 'expo-notifications';

class NotificationService {
  constructor() {
    this.notifications = [];
    this.isInitialized = false;
    this.useAsyncStorage = false;
    this.loadNotifications();
  }

  async initialize() {
    if (this.isInitialized) return;

    try {
      Notifications.setNotificationHandler({
        handleNotification: async () => ({
          shouldShowBanner: true,
          shouldShowList: true,
          shouldPlaySound: true,
          shouldSetBadge: true,
        }),
      });

      const { status } = await Notifications.requestPermissionsAsync();
      if (status !== 'granted') {
        return false;
      }

      this.isInitialized = true;
      return true;
    } catch (error) {
      return false;
    }
  }

  async triggerLEDAlert() {
    try {
      const timestamp = new Date();
      const notificationData = {
        id: Date.now().toString(),
        type: 'led_alert',
        title: '🚨 Device Movement Detected',
        body: 'Your GuardIt device has been moved or disturbed. Please check immediately.',
        timestamp: timestamp.toISOString(),
        date: timestamp.toLocaleDateString(),
        time: timestamp.toLocaleTimeString(),
        read: false
      };

      await Notifications.scheduleNotificationAsync({
        content: {
          title: notificationData.title,
          body: notificationData.body,
          data: notificationData,
          sound: 'default',
          priority: Notifications.AndroidNotificationPriority.HIGH,
        },
        trigger: null,
      });

      await this.addNotificationToHistory(notificationData);

      return notificationData;
    } catch (error) {
      return null;
    }
  }

  async addNotificationToHistory(notification) {
    try {
      this.notifications.unshift(notification);
      
      if (this.notifications.length > 100) {
        this.notifications = this.notifications.slice(0, 100);
      }
    } catch (error) {
    }
  }

  async loadNotifications() {
    this.notifications = [];
  }

  getNotifications() {
    return this.notifications;
  }

  getUnreadCount() {
    return this.notifications.filter(n => !n.read).length;
  }

  async markAsRead(notificationId) {
    try {
      const notification = this.notifications.find(n => n.id === notificationId);
      if (notification) {
        notification.read = true;
      }
    } catch (error) {
    }
  }

  async markAllAsRead() {
    try {
      this.notifications.forEach(n => n.read = true);
    } catch (error) {
    }
  }

  async clearAllNotifications() {
    try {
      this.notifications = [];
    } catch (error) {
    }
  }

  async deleteNotification(notificationId) {
    try {
      this.notifications = this.notifications.filter(n => n.id !== notificationId);
    } catch (error) {
    }
  }

  formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  }

  getNotificationsByType(type) {
    return this.notifications.filter(n => n.type === type);
  }

  getRecentNotifications() {
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    return this.notifications.filter(n => new Date(n.timestamp) > oneDayAgo);
  }
}

export default new NotificationService(); 
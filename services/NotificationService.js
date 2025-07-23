import * as Notifications from 'expo-notifications';

class NotificationService {
  constructor() {
    this.isInitialized = false;
    this.lastNotificationTime = 0;
    this.notificationCooldown = 2000;
    this.notifications = [];
  }

  async initialize() {
    if (this.isInitialized) {
      return true;
    }

    try {
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      
      let finalStatus = existingStatus;

      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        return false;
      }

      await Notifications.setNotificationHandler({
        handleNotification: async () => ({
          shouldShowAlert: true,
          shouldPlaySound: true,
          shouldSetBadge: false,
        }),
      });

      this.isInitialized = true;
      return true;
    } catch (error) {
      return false;
    }
  }

  async triggerLEDAlert() {
    const now = Date.now();
    if (now - this.lastNotificationTime < this.notificationCooldown) {
      return;
    }

    const timestamp = new Date().toLocaleTimeString();
    const success = await this.sendNotification(
      'LED Alert',
      `LED light has changed state at ${timestamp}`,
      { data: { type: 'led_alert', timestamp: now } }
    );

    if (success) {
      this.lastNotificationTime = now;
      await this.addNotificationToHistory({
        id: Date.now().toString(),
        title: 'LED Alert',
        body: `LED light has changed state at ${timestamp}`,
        type: 'led_alert',
        timestamp: now,
        read: false
      });
    }
  }

  async triggerBuzzerAlert() {
    const now = Date.now();
    if (now - this.lastNotificationTime < this.notificationCooldown) {
      return;
    }

    if (!this.isInitialized) {
      const initialized = await this.initialize();
      if (!initialized) {
        return;
      }
    }

    const timestamp = new Date().toLocaleTimeString();
    const success = await this.sendNotification(
      '📱 Device Movement Alert',
      `Unusual device movement detected at ${timestamp}`,
      { data: { type: 'motion_alert', timestamp: now } }
    );

    if (success) {
      this.lastNotificationTime = now;
      await this.addNotificationToHistory({
        id: Date.now().toString(),
        title: '📱 Device Movement Alert',
        body: `Unusual device movement detected at ${timestamp}`,
        type: 'motion_alert',
        timestamp: now,
        read: false
      });
    }
  }

  async triggerSuspiciousActivityAlert() {
    const now = Date.now();
    if (now - this.lastNotificationTime < this.notificationCooldown) {
      return;
    }

    if (!this.isInitialized) {
      const initialized = await this.initialize();
      if (!initialized) {
        return;
      }
    }

    const timestamp = new Date().toLocaleTimeString();
    const success = await this.sendNotification(
      'Suspicious Activity Detected',
      `Suspicious activity detected at ${timestamp}`,
      { data: { type: 'suspicious_activity', timestamp: now } }
    );

    if (success) {
      this.lastNotificationTime = now;
      await this.addNotificationToHistory({
        id: Date.now().toString(),
        title: 'Suspicious Activity Detected',
        body: `Suspicious activity detected at ${timestamp}`,
        type: 'suspicious_activity',
        timestamp: now,
        read: false
      });
    }
  }

  async triggerProximityAlert() {
    const now = Date.now();
    if (now - this.lastNotificationTime < this.notificationCooldown) {
      return;
    }

    if (!this.isInitialized) {
      const initialized = await this.initialize();
      if (!initialized) {
        return;
      }
    }

    const timestamp = new Date().toLocaleTimeString();
    const success = await this.sendNotification(
      '⚠️ Proximity Warning',
      `Person detected too close to camera at ${timestamp}`,
      { 
        data: { type: 'proximity_alert', timestamp: now },
        priority: Notifications.AndroidNotificationPriority.HIGH,
        vibrate: [0, 250, 250, 250, 250, 250],
        sound: true
      }
    );

    if (success) {
      this.lastNotificationTime = now;
      await this.addNotificationToHistory({
        id: Date.now().toString(),
        title: '⚠️ Proximity Warning',
        body: `Person detected too close to camera at ${timestamp}`,
        type: 'proximity_alert',
        timestamp: now,
        read: false
      });
    }
  }

  async sendNotification(title, body, options = {}) {
    try {
      const notificationId = await Notifications.scheduleNotificationAsync({
        content: {
          title,
          body,
          sound: true,
          priority: Notifications.AndroidNotificationPriority.HIGH,
          vibrate: [0, 250, 250, 250],
          ...options,
        },
        trigger: null,
      });
      return true;
    } catch (error) {
      return false;
    }
  }

  setNotificationCooldown(cooldownMs) {
    this.notificationCooldown = cooldownMs;
  }

  getUnreadCount() {
    return this.notifications.filter(n => !n.read).length;
  }

  getNotifications() {
    return this.notifications;
  }

  async addNotificationToHistory(notification) {
    try {
      this.notifications.unshift(notification);
      
      if (this.notifications.length > 100) {
        this.notifications = this.notifications.slice(0, 100);
      }
    } catch (error) {}
  }

  async markAsRead(notificationId) {
    try {
      const notification = this.notifications.find(n => n.id === notificationId);
      if (notification) {
        notification.read = true;
      }
    } catch (error) {}
  }

  async markAllAsRead() {
    try {
      this.notifications.forEach(n => n.read = true);
    } catch (error) {}
  }

  async clearAllNotifications() {
    try {
      this.notifications = [];
    } catch (error) {}
  }

  async deleteNotification(notificationId) {
    try {
      this.notifications = this.notifications.filter(n => n.id !== notificationId);
    } catch (error) {}
  }

  formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  }

  getNotificationsByType(type) {
    return this.notifications.filter(n => n.type === type);
  }

  getRecentNotifications() {
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    return this.notifications.filter(n => new Date(n.timestamp) > oneDayAgo);
  }
}

const notificationServiceInstance = new NotificationService();
export default notificationServiceInstance;

import * as Notifications from 'expo-notifications';

class CameraService {
  constructor() {
    this.baseURL = 'http://192.168.1.100:8090';
    this.isConnected = false;
    this.isStreaming = false;
    this.motionDetected = false;
    this.onMotionDetected = null;
    this.connectionTimeout = 5000;
  }

  setServerIP = (ipAddress) => {
    const cleanIP = ipAddress.replace(/^https?:\/\//, '');
    this.baseURL = `http://${cleanIP}:8090`;
  };

  testConnection = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.connectionTimeout);
      
      const response = await fetch(`${this.baseURL}/status`, {
        method: 'GET',
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        this.isConnected = data.camera_opened;
        this.isStreaming = data.is_streaming;
        return true;
      } else {
        this.isConnected = false;
        return false;
      }
    } catch (error) {
      this.isConnected = false;
      return false;
    }
  };

  startCamera = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.connectionTimeout);
      
      const response = await fetch(`${this.baseURL}/start`, {
        method: 'GET',
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        this.isStreaming = data.success;
        return data.success;
      } else {
        return false;
      }
    } catch (error) {
      return false;
    }
  };

  stopCamera = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.connectionTimeout);
      
      const response = await fetch(`${this.baseURL}/stop`, {
        method: 'GET',
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        this.isStreaming = false;
        return true;
      } else {
        return false;
      }
    } catch (error) {
      return false;
    }
  };

  getMotionDetection = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.connectionTimeout);
      
      const response = await fetch(`${this.baseURL}/detect`, {
        method: 'GET',
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        const wasMotionDetected = this.motionDetected;
        this.motionDetected = data.motion_detected;
        
        if (this.motionDetected && !wasMotionDetected) {
          this.triggerMotionAlert();
        }
        
        return data;
      } else {
        return null;
      }
    } catch (error) {
      return null;
    }
  };

  getCameraSettings = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.connectionTimeout);
      
      const response = await fetch(`${this.baseURL}/settings`, {
        method: 'GET',
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        return null;
      }
    } catch (error) {
      return null;
    }
  };

  updateCameraSettings = async (settings) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.connectionTimeout);
      
      const response = await fetch(`${this.baseURL}/settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        return data.success;
      } else {
        return false;
      }
    } catch (error) {
      return false;
    }
  };

  triggerMotionAlert = async () => {
    try {
      await Notifications.scheduleNotificationAsync({
        content: {
          title: '🚨 Motion Detected!',
          body: 'Movement detected by your GuardIt security camera. Check the live feed immediately.',
          data: { type: 'motion', source: 'camera' },
        },
        trigger: null,
      });
      
      if (this.onMotionDetected) {
        this.onMotionDetected();
      }
    } catch (error) {}
  };

  getStreamURL = () => {
    return `${this.baseURL}/stream`;
  };

  setMotionCallback = (callback) => {
    this.onMotionDetected = callback;
  };

  getConnectionStatus = () => {
    return this.isConnected;
  };

  getStreamingStatus = () => {
    return this.isStreaming;
  };

  getMotionStatus = () => {
    return this.motionDetected;
  };

  getDetectionStats = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.connectionTimeout);
      
      const response = await fetch(`${this.baseURL}/status`, {
        method: 'GET',
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        return {
          detection_model_loaded: data.detection_model_loaded,
          active_tracks: data.active_tracks,
          is_detecting: data.is_detecting,
          camera_settings: data.camera_settings
        };
      } else {
        return null;
      }
    } catch (error) {
      return null;
    }
  };

  takeScreenshot = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.connectionTimeout);
      
      const response = await fetch(`${this.baseURL}/screenshot`, {
        method: 'GET',
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        return null;
      }
    } catch (error) {
      return null;
    }
  };

  destroy = () => {
    this.isConnected = false;
    this.isStreaming = false;
    this.motionDetected = false;
    this.onMotionDetected = null;
  };
}

export default new CameraService(); 
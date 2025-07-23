import * as Notifications from 'expo-notifications';
import NotificationService from './NotificationService';

class WiFiService {
  constructor() {
    this.baseURL = 'http://10.103.135.13:8080';
    this.isConnected = false;
    this.pollingInterval = null;
    this.onDataReceived = null;
    this.lastData = null;
    this.connectionTimeout = 5000;
    this.lastBuzzerState = false;
  }

  setArduinoIP = (ipAddress) => {
    const cleanIP = ipAddress.replace(/^https?:\/\//, '');
    
    if (cleanIP.includes(':')) {
      this.baseURL = `http://${cleanIP}`;
    } else {
      this.baseURL = `http://${cleanIP}:8080`;
    }
  };

  testConnection = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.connectionTimeout);
      
      const response = await fetch(`${this.baseURL}/`, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        this.isConnected = true;
        return true;
      } else {
        this.isConnected = false;
        return false;
      }
    } catch (error) {
      this.isConnected = false;
      if (error.name === 'AbortError') {
        return await this.tryAlternativeEndpoints();
      } else {
        return false;
      }
    }
  };

  tryAlternativeEndpoints = async () => {
    const alternativeEndpoints = ['/imu', '/camera/info', '/'];
    const alternativePorts = [8000, 8080];
    
    for (const port of alternativePorts) {
      const baseURLWithPort = this.baseURL.replace(/:\d+/, '') + `:${port}`;
      
      for (const endpoint of alternativeEndpoints) {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 3000);
          
          const response = await fetch(`${baseURLWithPort}${endpoint}`, {
            method: 'GET',
            signal: controller.signal,
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
            },
          });
          
          clearTimeout(timeoutId);
          
          if (response.ok) {
            this.isConnected = true;
            this.baseURL = baseURLWithPort;
            return true;
          }
        } catch (error) {
          continue;
        }
      }
    }
    
    return false;
  };

  getIMUData = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.connectionTimeout);
      
      const response = await fetch(`${this.baseURL}/imu`, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        this.lastData = data;
        this.handleIMUData(data);
        return data;
      } else {
        return await this.getIMUDataFromAlternativeEndpoints();
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        return await this.getIMUDataFromAlternativeEndpoints();
      } else {
      return null;
    }
    }
  };

  getIMUDataFromAlternativeEndpoints = async () => {
    const alternativeEndpoints = ['/camera/info', '/'];
    const alternativePorts = [8000, 8080];
    
    for (const port of alternativePorts) {
      const baseURLWithPort = this.baseURL.replace(/:\d+/, '') + `:${port}`;
      
      for (const endpoint of alternativeEndpoints) {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 3000);
          
          const response = await fetch(`${baseURLWithPort}${endpoint}`, {
            method: 'GET',
            signal: controller.signal,
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
            },
          });
          
          clearTimeout(timeoutId);
          
          if (response.ok) {
            const data = await response.json();
            this.lastData = data;
            this.handleIMUData(data);
            this.baseURL = baseURLWithPort;
            return data;
          }
        } catch (error) {
          continue;
        }
      }
    }
    
    return null;
  };

  startPolling = (intervalMs = 1000) => {
      this.stopPolling();
    this.lastBuzzerState = false;
    
    this.pollingInterval = setInterval(async () => {
      try {
        const imuData = await this.getIMUData();
        if (imuData) {
          this.handleIMUData(imuData);
        }
        
        await this.checkDetectionAlerts();
      } catch (error) {
      }
    }, intervalMs);
  };

  stopPolling = () => {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  };

  handleIMUData = (data) => {
    if (!data) {
      return;
    }
    
    let normalizedData = this.normalizeDataFormat(data);
    
    if (!normalizedData) {
      return;
    }
    
    if (data.alert === true && !this.lastBuzzerState) {
      this.triggerBuzzerAlert();
      this.lastBuzzerState = true;
    } else if (data.alert === false) {
      this.lastBuzzerState = false;
    }
    
    if (data.alertType === 'suspicious_activity') {
      this.triggerSuspiciousActivityAlert();
    }
    
    if (data.alertType === 'proximity_alert') {
      this.triggerProximityAlert();
    }
    
    if (this.onDataReceived) {
      this.onDataReceived(normalizedData);
    }
  };

  triggerBuzzerAlert = async () => {
    try {
      const result = await NotificationService.triggerBuzzerAlert();
      return result;
    } catch (error) {
    }
  };

  triggerSuspiciousActivityAlert = async () => {
    try {
      const timestamp = new Date().toLocaleTimeString();
      
      const alertData = {
        title: '🚨 Suspicious Activity Detected',
        message: `Suspicious activity was detected at ${timestamp}`,
        type: 'suspicious_activity',
        timestamp: Date.now()
      };
      
      this.lastSuspiciousActivityAlert = alertData;
      
      if (this.onSuspiciousActivityAlert) {
        this.onSuspiciousActivityAlert(alertData);
      }
      
      return true;
    } catch (error) {
      return false;
      }
  };

  triggerProximityAlert = async () => {
    try {
      const result = await NotificationService.triggerProximityAlert();
      
      const timestamp = new Date().toLocaleTimeString();
      
      const alertData = {
        title: '⚠️ Proximity Warning',
        message: `Person detected too close to camera at ${timestamp}`,
        type: 'proximity_alert',
        timestamp: Date.now()
      };
      
      this.lastProximityAlert = alertData;
      
      if (this.onProximityAlert) {
        this.onProximityAlert(alertData);
      }
      
      return result;
    } catch (error) {
      return false;
    }
  };

  activateBuzzer = async (frequency = 1000, duration = 1.0) => {
    try {
      const response = await fetch(`${this.baseURL}/buzzer`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          frequency: frequency,
          duration: duration
        }),
      });
      
      if (response.ok) {
        const responseData = await response.json();
        
        setTimeout(() => {
          this.triggerBuzzerAlert();
        }, 100);
        return true;
      } else {
        const errorText = await response.text();
        
        this.triggerBuzzerAlert();
        return false;
      }
    } catch (error) {
      this.triggerBuzzerAlert();
      return false;
    }
  };

  normalizeDataFormat = (data) => {
    if (data.data && data.data.accelerometer) {
      const accel = data.data.accelerometer;
      const gyro = data.data.gyroscope || { x: 0, y: 0, z: 0 };
      const temp = data.data.temperature || 25;
      
      const magnitude = Math.sqrt(accel.x * accel.x + accel.y * accel.y + accel.z * accel.z);
      
      return {
        ax: accel.x,
        ay: accel.y,
        az: accel.z,
        gx: gyro.x,
        gy: gyro.y,
        gz: gyro.z,
        temp: temp,
        timestamp: Date.now(),
        magnitude: magnitude,
        change: magnitude
      };
    }
    
    if (data.accelerometer && typeof data.accelerometer.x !== 'undefined') {
      return {
        ax: data.accelerometer.x,
        ay: data.accelerometer.y,
        az: data.accelerometer.z,
        gx: 0,
        gy: 0,
        gz: 0,
        temp: 25,
        timestamp: data.timestamp || Date.now(),
        magnitude: data.accelerometer.magnitude,
        change: data.accelerometer.change
      };
    }
    
    if (typeof data.ax !== 'undefined' && typeof data.ay !== 'undefined' && typeof data.az !== 'undefined') {
      const magnitude = Math.sqrt(data.ax * data.ax + data.ay * data.ay + data.az * data.az);
      
      return {
        ...data,
        magnitude: magnitude,
        change: magnitude,
        timestamp: data.timestamp || Date.now()
      };
    }
    
    return null;
  };

  detectFall = (data) => {
    if (data.magnitude) {
      const fallThreshold = 20;
      return data.magnitude > fallThreshold;
    }
    
    const { ax, ay, az } = data;
    const magnitude = Math.sqrt(ax * ax + ay * ay + az * az);
    const fallThreshold = 20;
    return magnitude > fallThreshold;
  };

  detectUnusualMovement = (data) => {
    if (data.change) {
      const movementThreshold = 0.1;
      const isMovement = data.change > movementThreshold;
      return isMovement;
    }
    
    const { gx, gy, gz } = data;
    if (gx !== undefined && gy !== undefined && gz !== undefined) {
    const gyroMagnitude = Math.sqrt(gx * gx + gy * gy + gz * gz);
    const movementThreshold = 5;
    return gyroMagnitude > movementThreshold;
    }
    
    return false;
  };

  triggerFallAlert = async (data) => {
    try {
      await NotificationService.triggerLEDAlert();
    } catch (error) {
      return false;
    }
  };

  async activateBuzzer(frequency = 1000, duration = 2000) {
    try {
      const response = await fetch(`${this.baseURL}/buzzer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          frequency: frequency,
          duration: duration,
        }),
      });

      if (response.ok) {
        const responseData = await response.json();
        
        setTimeout(() => {
          this.triggerBuzzerAlert();
        }, 500);
        
        return true;
      } else {
        const errorText = await response.text();
        
        this.triggerBuzzerAlert();
        
        return false;
      }
    } catch (error) {
    }
  };

  setDataCallback = (callback) => {
    this.onDataReceived = callback;
  };

  setSuspiciousActivityAlertCallback = (callback) => {
    this.onSuspiciousActivityAlert = callback;
  };

  setProximityAlertCallback = (callback) => {
    this.onProximityAlert = callback;
  };

  getConnectionStatus = () => {
    return this.isConnected;
  };

  getLastData = () => {
    return this.lastData;
  };

  getBaseURL = () => {
    return this.baseURL;
  };

  enableDetection = async () => {
    try {
      const response = await fetch(`${this.baseURL}/detection/enable`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        return true;
      } else {
        return false;
      }
    } catch (error) {
      return false;
    }
  };

  disableDetection = async () => {
    try {
      const response = await fetch(`${this.baseURL}/detection/disable`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        return true;
      } else {
        return false;
      }
    } catch (error) {
      return false;
    }
  };

  getDetectionStatus = async () => {
    try {
      const response = await fetch(`${this.baseURL}/detection/status`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      
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

  checkDetectionAlerts = async () => {
    try {
      const detectionStatus = await this.getDetectionStatus();
      
      if (detectionStatus && detectionStatus.enabled) {
        if (detectionStatus.last_detection) {
          const lastDetectionTime = detectionStatus.last_detection * 1000;
          const currentTime = Date.now();
          const timeDiff = currentTime - lastDetectionTime;
          
          if (timeDiff < 5000) {
            await this.triggerSuspiciousActivityAlert();
          }
        }
      }
    } catch (error) {
    }
  };

  destroy = () => {
    this.stopPolling();
  }
}

export default new WiFiService();

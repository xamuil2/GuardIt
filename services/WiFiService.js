import * as Notifications from 'expo-notifications';
import NotificationService from './NotificationService';

class WiFiService {
  constructor() {
    this.baseURL = 'http://192.168.1.100';
    this.isConnected = false;
    this.pollingInterval = null;
    this.onDataReceived = null;
    this.lastData = null;
    this.connectionTimeout = 5000;
    this.lastLEDState = false;
    this.lastChangeValues = [];
    this.isLEDRed = false;
    this.lastSpikeTime = 0;
  }

  setArduinoIP = (ipAddress) => {
    const cleanIP = ipAddress.replace(/^https?:\/\//, '');
    
    if (cleanIP.includes(':')) {
      this.baseURL = `http://${cleanIP}`;
    } else {
    this.baseURL = `http://${cleanIP}`;
    }
  };

  testConnection = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.connectionTimeout);
      
      const response = await fetch(`${this.baseURL}/status`, {
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
    const alternativeEndpoints = ['/imu', '/data', '/sensor', '/'];
    const alternativePorts = [80, 8080];
    
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
    const alternativeEndpoints = ['/data', '/sensor', '/'];
    const alternativePorts = [80, 8080];
    
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
    if (this.pollingInterval) {
      this.stopPolling();
    }
    
    this.pollingInterval = setInterval(async () => {
      await this.getIMUData();
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
    
    const currentLEDState = data.alert?.active || false;
    
    if (currentLEDState !== this.lastLEDState) {
    }
    
    if (currentLEDState === true && this.lastLEDState === false) {
      this.triggerLEDAlert(normalizedData);
    }
    
    this.lastLEDState = currentLEDState;
    
    if (data.alert === true) {
      this.triggerLEDAlert(normalizedData);
    }
    
    if (data.alert && data.alert.shake_detected === true) {
      this.triggerLEDAlert(normalizedData);
    }
    
    if (data.accelerometer && data.accelerometer.change && data.alert && data.alert.threshold) {
      const change = data.accelerometer.change;
      const threshold = data.alert.threshold;
      const isAboveThreshold = change > threshold;
      
      if (isAboveThreshold) {
        this.triggerLEDAlert(normalizedData);
      }
    }
    
    if (data.accelerometer && data.accelerometer.change) {
      const change = data.accelerometer.change;
      
      this.lastChangeValues.push(change);
      if (this.lastChangeValues.length > 5) {
        this.lastChangeValues.shift();
      }
      
      const spikeThreshold = 0.01;
      const isSignificantSpike = change > spikeThreshold;
      
      if (this.lastChangeValues.length >= 2) {
        const recentChanges = this.lastChangeValues.slice(-2);
        const averageChange = recentChanges.reduce((sum, val) => sum + val, 0) / recentChanges.length;
        
        if (isSignificantSpike && !this.isLEDRed) {
          this.isLEDRed = true;
          this.lastSpikeTime = Date.now();
          this.triggerLEDAlert(normalizedData);
        }
        
        if (this.isLEDRed && averageChange < 0.005) {
          this.isLEDRed = false;
        }
      }
    }
    
    if (data.accelerometer && data.accelerometer.magnitude) {
      const magnitude = data.accelerometer.magnitude;
      const magnitudeThreshold = 1.1;
      const isHighAcceleration = Math.abs(magnitude - 1.0) > 0.1;
      
      if (isHighAcceleration) {
        this.triggerLEDAlert(normalizedData);
      }
    }
    
    if (data.accelerometer && data.accelerometer.change && !this.isLEDRed) {
      const change = data.accelerometer.change;
      const backupThreshold = 0.01;
      const isSignificantMovement = change > backupThreshold;
      
      if (isSignificantMovement) {
        this.triggerLEDAlert(normalizedData);
      }
    }
    
    if (this.detectFall(normalizedData)) {
      this.triggerFallAlert(normalizedData);
    }
    
    if (this.detectUnusualMovement(normalizedData)) {
      this.triggerMovementAlert(normalizedData);
    }
    
    if (this.onDataReceived) {
      this.onDataReceived(normalizedData);
    }
  };

  triggerLEDAlert = async (data) => {
    try {
      const result = await NotificationService.triggerLEDAlert();
      return result;
    } catch (error) {
    }
  };

  normalizeDataFormat = (data) => {
    if (data.accelerometer && typeof data.accelerometer.x !== 'undefined') {
      return {
        ax: data.accelerometer.x,
        ay: data.accelerometer.y,
        az: data.accelerometer.z,
        gx: 0,
        gy: 0,
        gz: 0,
        temp: 25,
        alert: data.alert?.active || false,
        alert_type: data.alert?.shake_detected ? 'shake' : '',
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
    }
  };

  triggerMovementAlert = async (data) => {
    try {
      await NotificationService.triggerLEDAlert();
    } catch (error) {
    }
  };

  setDataCallback = (callback) => {
    this.onDataReceived = callback;
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

  destroy = () => {
    this.stopPolling();
    this.isConnected = false;
    this.onDataReceived = null;
  };
}

export default new WiFiService(); 
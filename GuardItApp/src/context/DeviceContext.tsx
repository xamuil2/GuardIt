import React, { createContext, useContext, useState, useEffect } from 'react';

interface DeviceStatus {
  isConnected: boolean;
  isActive: boolean;
  batteryLevel: number;
  lastSeen: Date;
  motionDetected: boolean;
  suspiciousActivity: boolean;
}

interface DeviceContextType {
  deviceStatus: DeviceStatus;
  activateDevice: () => Promise<void>;
  deactivateDevice: () => Promise<void>;
  ringAlarm: () => Promise<void>;
  connectDevice: () => Promise<void>;
  disconnectDevice: () => Promise<void>;
}

const DeviceContext = createContext<DeviceContextType | undefined>(undefined);

export const useDevice = () => {
  const context = useContext(DeviceContext);
  if (context === undefined) {
    throw new Error('useDevice must be used within a DeviceProvider');
  }
  return context;
};

export const DeviceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [deviceStatus, setDeviceStatus] = useState<DeviceStatus>({
    isConnected: false,
    isActive: false,
    batteryLevel: 85,
    lastSeen: new Date(),
    motionDetected: false,
    suspiciousActivity: false,
  });

  useEffect(() => {
    // Simulate device connection status updates
    const interval = setInterval(() => {
      setDeviceStatus(prev => ({
        ...prev,
        lastSeen: new Date(),
        batteryLevel: Math.max(0, prev.batteryLevel - 1),
      }));
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const activateDevice = async () => {
    try {
      // Simulate API call to activate device
      await new Promise(resolve => setTimeout(resolve, 500));
      setDeviceStatus(prev => ({
        ...prev,
        isActive: true,
      }));
    } catch (error) {
      console.error('Error activating device:', error);
    }
  };

  const deactivateDevice = async () => {
    try {
      // Simulate API call to deactivate device
      await new Promise(resolve => setTimeout(resolve, 500));
      setDeviceStatus(prev => ({
        ...prev,
        isActive: false,
        motionDetected: false,
        suspiciousActivity: false,
      }));
    } catch (error) {
      console.error('Error deactivating device:', error);
    }
  };

  const ringAlarm = async () => {
    try {
      // Simulate API call to ring alarm
      await new Promise(resolve => setTimeout(resolve, 200));
      console.log('Alarm ringing on device!');
    } catch (error) {
      console.error('Error ringing alarm:', error);
    }
  };

  const connectDevice = async () => {
    try {
      // Simulate device connection
      await new Promise(resolve => setTimeout(resolve, 1000));
      setDeviceStatus(prev => ({
        ...prev,
        isConnected: true,
      }));
    } catch (error) {
      console.error('Error connecting device:', error);
    }
  };

  const disconnectDevice = async () => {
    try {
      // Simulate device disconnection
      await new Promise(resolve => setTimeout(resolve, 500));
      setDeviceStatus(prev => ({
        ...prev,
        isConnected: false,
        isActive: false,
      }));
    } catch (error) {
      console.error('Error disconnecting device:', error);
    }
  };

  const value = {
    deviceStatus,
    activateDevice,
    deactivateDevice,
    ringAlarm,
    connectDevice,
    disconnectDevice,
  };

  return (
    <DeviceContext.Provider value={value}>
      {children}
    </DeviceContext.Provider>
  );
}; 
# GuardIt Raspberry Pi to iOS App Setup Guide

## 🚀 Quick Setup Steps

### 1. Prepare Raspberry Pi
```bash
cd /home/guardit/Documents/GuardIt/raspberry-pi-iot

# Install required packages (if not already installed)
pip3 install smbus2 flask RPi.GPIO

# Make scripts executable
chmod +x *.py
```

### 2. Get Raspberry Pi IP Address
```bash
# Run this to get your Pi's IP address
python3 get_pi_ip.py
```

### 3. Start the IMU Server
```bash
# Option 1: Use the launcher (recommended)
python3 start_guardit_server.py

# Option 2: Start directly
python3 imu_wifi_server.py
```

### 4. Configure iOS App
1. Open the GuardIt iOS app
2. Go to the IMU Screen
3. In the IP address field, enter your Pi's IP:
   - Example: `192.168.1.100:8080`
   - Or just: `192.168.1.100` (port 8080 will be auto-added)
4. Tap "Connect to Arduino" (button works for Pi too!)

### 5. Verify Connection
- ✅ Status should show "Connected"
- ✅ Device type should show "Raspberry Pi Device"
- ✅ Port should show "8080"
- ✅ IMU data should start streaming

## 🔧 Troubleshooting

### Common Issues:

1. **Connection Failed**
   - Check both devices are on same WiFi network
   - Verify Pi IP address with `python3 get_pi_ip.py`
   - Ensure IMU server is running
   - Try adding `:8080` to the IP address

2. **IMU Data Not Reading**
   - Check I2C is enabled: `sudo raspi-config` → Interface Options → I2C → Enable
   - Verify MPU6050 is connected properly
   - Check hardware connections (see HARDWARE_PINOUT.md)

3. **Server Won't Start**
   - Install missing packages: `pip3 install smbus2 flask RPi.GPIO`
   - Check GPIO permissions: `sudo usermod -a -G gpio $USER`
   - Try running with sudo: `sudo python3 imu_wifi_server.py`

## 📡 Network Configuration

### Default Settings:
- **Port**: 8080 (Raspberry Pi) / 80 (Arduino)
- **Endpoints**: `/status`, `/imu`, `/data`, `/sensor`
- **Auto-discovery**: App tries both ports automatically

### iOS App Features:
- ✅ Auto-detects device type (Arduino vs Raspberry Pi)
- ✅ Auto-tries multiple ports (8080, 80)
- ✅ Shows connection status and device info
- ✅ Falls back to alternative endpoints if needed

## 🔄 Data Flow

```
Raspberry Pi (imu_wifi_server.py) 
    ↓ HTTP/JSON
iOS App (WiFiService.js)
    ↓ Polling every 500ms
IMU Screen Display
    ↓ Alerts/Notifications
NotificationService.js
```

## 🎯 Key Features Supported

✅ **IMU Data Streaming** - Accelerometer, Gyroscope, Temperature
✅ **Fall Detection** - Configurable threshold
✅ **Movement Detection** - Unusual movement alerts  
✅ **LED Feedback** - RGB LED status indication
✅ **Buzzer Alerts** - Audio alerts for events
✅ **Real-time Notifications** - iOS push notifications
✅ **Device Auto-detection** - Automatically detects Pi vs Arduino

## 📱 iOS App Updates

The iOS app now includes:
- Support for Raspberry Pi port 8080
- Device type detection and display
- Enhanced error messages
- Better connection retry logic
- Automatic port fallback

Ready to test your setup! 🛡️

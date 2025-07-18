# Arduino IMU Connection Troubleshooting Guide

This guide will help you fix the "Connection timeout - Arduino not responding" error and get your Arduino IMU sensor working with the GuardIt app.

## 🚨 Quick Fix Checklist

### 1. **Arduino Hardware Setup**
- [ ] Arduino/ESP32 is powered on
- [ ] MPU6050 sensor is properly connected
- [ ] USB cable is connected (for programming)
- [ ] Serial Monitor shows "WiFi connected" message

### 2. **WiFi Configuration**
- [ ] WiFi credentials are correct in Arduino code
- [ ] Both phone and Arduino are on same WiFi network
- [ ] WiFi signal is strong enough
- [ ] No firewall blocking port 80

### 3. **IP Address**
- [ ] IP address shown in Serial Monitor matches app
- [ ] IP address format is correct (e.g., 192.168.1.100)
- [ ] No extra spaces or characters in IP field

## 🔧 Step-by-Step Troubleshooting

### Step 1: Verify Arduino Code

1. **Open Arduino IDE**
2. **Load the IMU_WiFi_Server.ino file**
3. **Update WiFi credentials:**
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
4. **Upload code to Arduino**
5. **Open Serial Monitor (115200 baud)**

### Step 2: Check Serial Monitor Output

**Expected output:**
```
GuardIt IMU WiFi Server Starting...
MPU6050 initialized successfully
Connecting to WiFi: YOUR_WIFI_SSID
WiFi connected!
IP address: 192.168.1.100
HTTP server started
Server IP: 192.168.1.100
Server Port: 80
Ready to receive connections from GuardIt app!
```

**If you see errors:**
- **"MPU6050 not found!"** → Check sensor connections
- **"WiFi connection failed!"** → Check WiFi credentials
- **No output** → Check USB connection and board selection

### Step 3: Test Arduino Server

1. **Note the IP address from Serial Monitor**
2. **Open web browser on your computer**
3. **Navigate to:** `http://[ARDUINO_IP]/status`
   - Example: `http://192.168.1.100/status`
4. **Expected response:**
   ```json
   {
     "connected": true,
     "ip": "192.168.1.100",
     "rssi": -45,
     "uptime": 1234
   }
   ```

### Step 4: Use App Diagnostics

1. **Open GuardIt app**
2. **Go to IMU Sensor screen**
3. **Enter the Arduino IP address**
4. **Tap "Diagnostics" button**
5. **Review the test results**

## 🛠️ Common Issues and Solutions

### Issue 1: "Connection timeout - Arduino not responding"

**Causes:**
- Arduino not powered on
- Wrong IP address
- Network connectivity issues
- Arduino code not uploaded

**Solutions:**
1. Check if Arduino is powered and Serial Monitor shows "WiFi connected"
2. Verify IP address matches Serial Monitor output
3. Ensure both devices are on same WiFi network
4. Re-upload Arduino code

### Issue 2: "Failed to connect to Arduino - HTTP error: 404"

**Causes:**
- Arduino server not running
- Wrong endpoint being called
- Arduino code issues

**Solutions:**
1. Check Serial Monitor for "HTTP server started" message
2. Verify Arduino code is uploaded correctly
3. Test with browser first: `http://[IP]/status`

### Issue 3: "WiFi connection failed"

**Causes:**
- Wrong WiFi credentials
- WiFi network not available
- Signal strength issues

**Solutions:**
1. Double-check SSID and password in Arduino code
2. Ensure WiFi network is 2.4GHz (some ESP32 boards don't support 5GHz)
3. Move Arduino closer to WiFi router
4. Try a different WiFi network

### Issue 4: "MPU6050 not found"

**Causes:**
- Incorrect wiring
- Sensor not powered
- I2C address conflict

**Solutions:**
1. Check wiring connections:
   - SDA → GPIO21 (ESP32) or GPIO4 (ESP8266)
   - SCL → GPIO22 (ESP32) or GPIO5 (ESP8266)
   - VCC → 3.3V
   - GND → GND
2. Verify sensor is getting power (check voltage)
3. Try different I2C pins if available

### Issue 5: App shows "Connection failed" after multiple retries

**Causes:**
- Network firewall blocking connections
- Port 80 blocked
- Router security settings

**Solutions:**
1. Check router firewall settings
2. Temporarily disable antivirus/firewall
3. Try connecting from computer browser first
4. Check if router blocks device-to-device communication

## 🔍 Advanced Diagnostics

### Network Testing

**From your computer:**
```bash
# Test basic connectivity
ping [ARDUINO_IP]

# Test HTTP connection
curl http://[ARDUINO_IP]/status

# Test port 80
telnet [ARDUINO_IP] 80
```

### Arduino Code Debugging

Add debug prints to Arduino code:
```cpp
void setup() {
  Serial.begin(115200);
  Serial.println("=== DEBUG MODE ===");
  
  // Test WiFi connection
  Serial.print("SSID: ");
  Serial.println(ssid);
  
  // Test sensor
  Serial.print("MPU6050 Address: 0x");
  Serial.println(MPU6050_ADDR, HEX);
}
```

### Alternative Connection Methods

If standard connection fails, try:
1. **Static IP assignment** in Arduino code
2. **Different port** (change from 80 to 8080)
3. **Access Point mode** (Arduino creates its own WiFi network)

## 📱 App-Specific Solutions

### Clear App Cache
1. Close GuardIt app completely
2. Clear app cache (Settings → Apps → GuardIt → Storage → Clear Cache)
3. Restart app

### Reset Connection Settings
1. Go to IMU Sensor screen
2. Tap "Disconnect" if connected
3. Clear IP address field
4. Re-enter IP address
5. Try connecting again

### Use Diagnostics Feature
1. Tap "Diagnostics" button
2. Review test results
3. Follow recommendations provided

## 🔧 Hardware Troubleshooting

### Check Physical Connections
1. **Power LED** should be on
2. **WiFi LED** should blink during connection
3. **USB connection** should be stable
4. **Sensor connections** should be secure

### Test with Different Hardware
1. Try different USB cable
2. Test with different Arduino board
3. Try different MPU6050 sensor
4. Test with different WiFi network

## 📞 Getting Help

If you're still having issues:

1. **Check Serial Monitor output** and note any error messages
2. **Take screenshot** of the error in the app
3. **Note your hardware setup** (Arduino model, sensor type)
4. **Test with browser** first to isolate app vs hardware issues
5. **Try the diagnostics feature** in the app

## ✅ Success Indicators

When everything is working correctly, you should see:

**In Serial Monitor:**
- "WiFi connected!"
- "HTTP server started"
- Regular sensor data output
- "FALL DETECTED!" when sensor is shaken

**In GuardIt App:**
- Status shows "Connected"
- Live sensor data updates
- No error messages
- Alerts trigger when sensor detects movement

**In Browser Test:**
- `http://[IP]/status` returns JSON response
- `http://[IP]/imu` returns sensor data

## 🎯 Quick Test Procedure

1. **Upload Arduino code** and verify Serial Monitor output
2. **Note IP address** from Serial Monitor
3. **Test in browser:** `http://[IP]/status`
4. **Enter IP in app** and tap "Connect"
5. **Tap "Start Polling"** to see live data
6. **Shake sensor** to test fall detection

If all steps work, your Arduino IMU sensor is properly connected to the GuardIt app! 🎉 
# Arduino Network Connectivity Debug Checklist

## Step 1: Verify Arduino WiFi Connection

### Check Serial Monitor Output
1. Open Arduino IDE
2. Connect your Arduino/ESP32 to your computer via USB
3. Open Serial Monitor (Tools > Serial Monitor)
4. Set baud rate to 115200
5. Look for these messages:
   ```
   GuardIt IMU WiFi Server Starting...
   MPU6050 initialized successfully
   Connecting to WiFi: Avnit
   WiFi connected!
   IP address: [some IP address]
   HTTP server started
   Server IP: [some IP address]
   Server Port: 80
   Ready to receive connections from GuardIt app!
   ```

### If Arduino Shows Different IP:
- The IP address shown in Serial Monitor is the correct one
- Update your app with this IP address
- The IP `172.20.10.11` might be incorrect

## Step 2: Network Configuration Issues

### Hotspot vs WiFi Network
Since you're using a hotspot:
1. **Check Hotspot Device Isolation**: Some hotspots have device isolation enabled
   - This prevents devices from seeing each other
   - Disable device isolation in your hotspot settings
   
2. **Check Hotspot IP Range**: 
   - Your Arduino shows IP `172.20.10.11`
   - This suggests your hotspot uses the `172.20.10.x` range
   - Make sure your phone/computer is also in this range

### Verify Both Devices on Same Network
1. On your phone/computer, check your IP address:
   - **iPhone**: Settings > WiFi > tap (i) next to network name
   - **Android**: Settings > Network & Internet > WiFi > tap network name
   - **Mac**: System Preferences > Network > WiFi > Advanced
   
2. Your device IP should be something like `172.20.10.x` (same subnet as Arduino)

## Step 3: Test Basic Connectivity

### Ping Test
Try pinging the Arduino from your computer:
```bash
ping 172.20.10.11
```

### Alternative IP Discovery
If the above IP doesn't work, try these common hotspot IPs:
- `192.168.1.1` (gateway)
- `192.168.1.100`
- `192.168.43.1` (Android hotspot gateway)
- `172.20.10.1` (your hotspot gateway)

## Step 4: Arduino Code Issues

### Check WiFi Credentials
In your Arduino code, verify:
```cpp
const char* ssid = "Avnit";        // Your hotspot name
const char* password = "hihihihi"; // Your hotspot password
```

### Check Server Port
The Arduino code should use:
```cpp
WebServer server(80);  // Port 80
const int SERVER_PORT = 80;
```

## Step 5: Firewall/Port Issues

### Check if Port 80 is Blocked
Some networks block port 80. Try changing Arduino to port 8080:
```cpp
WebServer server(8080);  // Change to port 8080
const int SERVER_PORT = 8080;
```

### Test with Different Port
If port 80 is blocked, the app will automatically try port 8080.

## Step 6: Alternative Testing

### Use Browser to Test
1. On your phone/computer, open a web browser
2. Navigate to: `http://[ARDUINO_IP]/`
3. You should see JSON response with server info

### Use Network Scanner
Download a network scanner app to find all devices on your network.

## Step 7: Common Solutions

### Solution 1: Disable Device Isolation
- Go to your hotspot device settings
- Find "Device Isolation" or "AP Isolation"
- Disable it

### Solution 2: Use Static IP
In Arduino code, set a static IP:
```cpp
IPAddress local_IP(172, 20, 10, 100);
IPAddress gateway(172, 20, 10, 1);
IPAddress subnet(255, 255, 255, 0);
WiFi.config(local_IP, gateway, subnet);
```

### Solution 3: Check Hotspot Settings
- Ensure hotspot allows device-to-device communication
- Check if there are any security settings blocking connections

## Step 8: Verification Steps

Once you fix the connection:
1. Run the test script: `python3 test_arduino_data.py`
2. Should show: "✅ Connection successful on port 80"
3. Should show live IMU data
4. App should connect and show sensor data

## Troubleshooting Commands

### Test from Terminal
```bash
# Test basic connectivity
curl http://172.20.10.11/

# Test specific endpoint
curl http://172.20.10.11/imu

# Test with timeout
curl --connect-timeout 5 http://172.20.10.11/
```

### Check Network Interface
```bash
# On Mac/Linux
ifconfig | grep "inet "

# On Windows
ipconfig
```

## Next Steps

1. **First**: Check Arduino Serial Monitor for correct IP
2. **Second**: Verify both devices are on same network
3. **Third**: Disable device isolation on hotspot
4. **Fourth**: Test with browser or curl
5. **Fifth**: Update app with correct IP
6. **Sixth**: Test with Python script
7. **Seventh**: Test with React Native app

Let me know what you find in the Arduino Serial Monitor! 
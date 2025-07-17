#include <Arduino.h>
#include <Wire.h>
#include <MPU9250_asukiaaa.h>
#include <SoftwareSerial.h>
#include <TinyGPS++.h>
#include <WiFiS3.h>
#include <ArduinoJson.h>

// WiFi credentials - UPDATE THESE WITH YOUR NETWORK
const char* ssid = "Avnit";     // Replace with your WiFi network name
const char* password = "hihihihi"; // Replace with your WiFi password

// WiFi server on port 80
WiFiServer server(80);

// JSON document for sending data
StaticJsonDocument<512> jsonDoc;

// MPU9250 sensor object
MPU9250_asukiaaa mpu;

// GPS objects - Grove GPS v1.1
TinyGPSPlus gps;
SoftwareSerial ss(4, 3);  // RX, TX pins for Grove GPS v1.1

// GPS debugging variables
unsigned long lastGPSDebug = 0;
const unsigned long GPS_DEBUG_INTERVAL = 10000;  // Debug info every 10 seconds
unsigned long gpsCharsProcessed = 0;
unsigned long lastGPSCharCount = 0;

// RGB LED pins
const int RED_PIN = 9;
const int GREEN_PIN = 10;
const int BLUE_PIN = 11;


// Buzzer pin
const int BUZZER_PIN = 8;

// Shake detection variables
const float SHAKE_THRESHOLD = 0.2;  // Adjust this value to change sensitivity (higher = less sensitive)
const unsigned long SHAKE_DEBOUNCE = 500;  // Minimum time between shake detections (ms)
unsigned long lastShakeTime = 0;

// Alert duration variables
const unsigned long ALERT_DURATION = 2000;  // How long to keep LED red and buzzer on (ms)
unsigned long alertStartTime = 0;
bool alertActive = false;

// GPS update variables
const unsigned long GPS_UPDATE_INTERVAL = 5000;  // Update GPS location every 5 seconds
unsigned long lastGPSUpdate = 0;

// Previous acceleration values for comparison
float prevAccelMagnitude = 0;

// GPS location variables
double currentLatitude = 0.0;
double currentLongitude = 0.0;
bool gpsLocationValid = false;

// Function to set RGB LED color
void setLEDColor(int red, int green, int blue) {
  analogWrite(RED_PIN, red);
  analogWrite(GREEN_PIN, green);
  analogWrite(BLUE_PIN, blue);
}

// Function to play alert buzzer
void playAlertBuzzer() {
  // Play a series of beeps
  for (int i = 0; i < 3; i++) {
    tone(BUZZER_PIN, 1000, 200);  // 1kHz tone for 200ms
    delay(100);
    noTone(BUZZER_PIN);
    delay(100);
  }
}

// Function to test GPS at different baud rates
void testGPSBaudRates() {
  Serial.println("🔍 Testing GPS baud rates...");
  Serial.println("Make sure GPS module has power and antenna is connected!");
  Serial.println();
  
  int baudRates[] = {4800, 9600, 38400};
  int numRates = sizeof(baudRates) / sizeof(baudRates[0]);
  
  for (int i = 0; i < numRates; i++) {
    Serial.print("Testing ");
    Serial.print(baudRates[i]);
    Serial.println(" baud...");
    
    ss.begin(baudRates[i]);
    delay(1000);  // Wait for GPS to stabilize
    
    unsigned long startTime = millis();
    int charCount = 0;
    bool foundNMEA = false;
    
    // Test for 3 seconds
    while (millis() - startTime < 3000) {
      if (ss.available() > 0) {
        char c = ss.read();
        charCount++;
        
        // Check for NMEA sentence start
        if (c == '$') {
          foundNMEA = true;
        }
        
        // Print first 100 characters for debugging
        if (charCount <= 100) {
          Serial.print(c);
        }
      }
    }
    
    Serial.println();
    Serial.print("Characters received: ");
    Serial.println(charCount);
    
    if (foundNMEA) {
      Serial.println("✅ Found NMEA sentences (GPS data format)");
    }
    
    if (charCount > 0) {
      Serial.print("✅ Found GPS data at ");
      Serial.print(baudRates[i]);
      Serial.println(" baud!");
      if (foundNMEA) {
        Serial.println("✅ NMEA format detected - GPS is working!");
      }
      return;  // Exit on first successful baud rate
    }
    
    Serial.println("❌ No data at this baud rate");
    Serial.println();
  }
  
  Serial.println("❌ No GPS data found at any tested baud rate");
  Serial.println();
  Serial.println("🔧 TROUBLESHOOTING STEPS:");
  Serial.println("1. Check power: GPS needs 5V, not 3.3V");
  Serial.println("2. Check wiring:");
  Serial.println("   GPS VCC → Arduino 5V");
  Serial.println("   GPS GND → Arduino GND");
  Serial.println("   GPS TX → Arduino pin 4");
  Serial.println("   GPS RX → Arduino pin 3");
  Serial.println("3. Ensure antenna is connected and has clear sky view");
  Serial.println("4. GPS module should have a blinking LED when searching");
  Serial.println("5. Try outdoors - GPS doesn't work indoors");
}

// Function to setup WiFi connection
void setupWiFi() {
  Serial.print("Connecting to WiFi network: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi connected successfully!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("SSID: ");
    Serial.println(WiFi.SSID());
    Serial.print("Signal strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    
    // Start the server
    server.begin();
    Serial.println("✅ HTTP server started on port 80");
    Serial.println("📱 iOS app can connect to: http://" + WiFi.localIP().toString());
  } else {
    Serial.println();
    Serial.println("❌ WiFi connection failed!");
    Serial.println("Please check your WiFi credentials and try again.");
    setLEDColor(255, 0, 0);  // Red for WiFi error
  }
}

// Function to create JSON response with sensor data
String createSensorDataJSON() {
  // Clear the JSON document
  jsonDoc.clear();
  
  // Add timestamp
  jsonDoc["timestamp"] = millis();
  
  // Add accelerometer data
  JsonObject accel = jsonDoc.createNestedObject("accelerometer");
  mpu.accelUpdate();
  accel["x"] = mpu.accelX();
  accel["y"] = mpu.accelY();
  accel["z"] = mpu.accelZ();
  
  // Calculate and add acceleration magnitude and change
  float accelMagnitude = sqrt(pow(mpu.accelX(), 2) + pow(mpu.accelY(), 2) + pow(mpu.accelZ(), 2));
  float accelChange = abs(accelMagnitude - prevAccelMagnitude);
  accel["magnitude"] = accelMagnitude;
  accel["change"] = accelChange;
  
  // Add GPS data
  JsonObject gps_data = jsonDoc.createNestedObject("gps");
  gps_data["valid"] = gpsLocationValid;
  if (gpsLocationValid) {
    gps_data["latitude"] = currentLatitude;
    gps_data["longitude"] = currentLongitude;
    if (gps.altitude.isValid()) {
      gps_data["altitude"] = gps.altitude.meters();
    }
    if (gps.speed.isValid()) {
      gps_data["speed"] = gps.speed.kmph();
    }
    if (gps.satellites.isValid()) {
      gps_data["satellites"] = gps.satellites.value();
    }
  }
  
  // Add alert status
  JsonObject alert = jsonDoc.createNestedObject("alert");
  alert["active"] = alertActive;
  alert["shake_detected"] = (accelChange > SHAKE_THRESHOLD);
  alert["threshold"] = SHAKE_THRESHOLD;
  
  // Add device status
  JsonObject status = jsonDoc.createNestedObject("status");
  status["wifi_connected"] = (WiFi.status() == WL_CONNECTED);
  status["wifi_rssi"] = WiFi.RSSI();
  status["gps_chars_processed"] = gpsCharsProcessed;
  status["gps_sentences_passed"] = gps.passedChecksum();
  status["gps_sentences_failed"] = gps.failedChecksum();
  
  // Convert to string
  String jsonString;
  serializeJson(jsonDoc, jsonString);
  return jsonString;
}

// Function to handle HTTP requests
void handleHTTPRequests() {
  WiFiClient client = server.available();
  
  if (client) {
    Serial.println("📱 New client connected");
    String request = "";
    
    // Read the request
    while (client.connected() && client.available()) {
      char c = client.read();
      request += c;
      if (request.endsWith("\r\n\r\n")) {
        break;
      }
    }
    
    // Parse the request
    String path = "/";
    int pathStart = request.indexOf(' ') + 1;
    int pathEnd = request.indexOf(' ', pathStart);
    if (pathStart > 0 && pathEnd > pathStart) {
      path = request.substring(pathStart, pathEnd);
    }
    
    Serial.print("📡 Request: ");
    Serial.println(path);
    
    // Handle different endpoints
    if (path == "/" || path == "/status") {
      // Main status endpoint
      String jsonResponse = createSensorDataJSON();
      
      // Send HTTP response
      client.println("HTTP/1.1 200 OK");
      client.println("Content-Type: application/json");
      client.println("Access-Control-Allow-Origin: *");
      client.println("Access-Control-Allow-Methods: GET, POST, OPTIONS");
      client.println("Access-Control-Allow-Headers: Content-Type");
      client.println("Connection: close");
      client.println();
      client.println(jsonResponse);
      
    } else if (path == "/alert") {
      // Alert endpoint - only send if alert is active
      JsonObject response = jsonDoc.createNestedObject("alert_response");
      response["alert_active"] = alertActive;
      response["timestamp"] = millis();
      if (alertActive) {
        response["location"]["latitude"] = currentLatitude;
        response["location"]["longitude"] = currentLongitude;
        response["location"]["valid"] = gpsLocationValid;
      }
      
      String jsonResponse;
      serializeJson(jsonDoc, jsonResponse);
      
      client.println("HTTP/1.1 200 OK");
      client.println("Content-Type: application/json");
      client.println("Access-Control-Allow-Origin: *");
      client.println("Connection: close");
      client.println();
      client.println(jsonResponse);
      
    } else {
      // 404 Not Found
      client.println("HTTP/1.1 404 Not Found");
      client.println("Content-Type: text/plain");
      client.println("Connection: close");
      client.println();
      client.println("Endpoint not found");
    }
    
    client.stop();
    Serial.println("📱 Client disconnected");
  }
}

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Initialize Grove GPS v1.1 serial communication
  ss.begin(9600);
  
  // Initialize RGB LED pins
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  
  // Initialize buzzer pin
  pinMode(BUZZER_PIN, OUTPUT);
  
  // Set initial LED state (green = ready)
  setLEDColor(0, 255, 0);  // Green
  
  // Initialize I2C communication
  Wire.begin();
  
  // Add I2C scanner to check for devices
  Serial.println("Scanning I2C bus for devices...");
  int deviceCount = 0;
  for(byte address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    if(Wire.endTransmission() == 0) {
      Serial.print("I2C device found at address 0x");
      if(address < 16) Serial.print("0");
      Serial.println(address, HEX);
      deviceCount++;
    }
  }
  if(deviceCount == 0) {
    Serial.println("No I2C devices found! Check wiring.");
  } else {
    Serial.print("Found ");
    Serial.print(deviceCount);
    Serial.println(" I2C device(s).");
  }
  
  // Initialize MPU9250
  Serial.println("Initializing MPU9250...");
  mpu.setWire(&Wire);
  
  // Initialize components
  Serial.println("Initializing accelerometer...");
  mpu.beginAccel();
  
  Serial.println("Initializing gyroscope...");
  mpu.beginGyro();
  
  Serial.println("Initializing magnetometer...");
  mpu.beginMag();
  
  // Add a small delay for initialization
  delay(100);
  
  // Check if MPU9250 is connected
  uint8_t sensorId;
  Serial.println("Reading sensor ID...");
  Serial.println("✓ MPU9250 detected at I2C address 0x68");
  
  if (mpu.readId(&sensorId) == 0) {
    Serial.print("Sensor ID read successfully: 0x");
    Serial.println(sensorId, HEX);
    
    // MPU9250 can have different IDs: 0x71 (most common), 0x73, or 0x68
    if (sensorId == 0x71 || sensorId == 0x73 || sensorId == 0x68) {
      Serial.println("MPU9250 connection successful");
    } else {
      Serial.print("Unexpected sensor ID. Expected 0x68, 0x71, or 0x73, got 0x");
      Serial.println(sensorId, HEX);
      Serial.println("Proceeding anyway - sensor may still work...");
    }
    
    // Test accelerometer reading regardless of sensor ID
    Serial.println("Testing accelerometer reading...");
    mpu.accelUpdate();
    float testX = mpu.accelX();
    float testY = mpu.accelY();
    float testZ = mpu.accelZ();
    
    Serial.print("Test reading - X: ");
    Serial.print(testX);
    Serial.print(", Y: ");
    Serial.print(testY);
    Serial.print(", Z: ");
    Serial.println(testZ);
    
    // Check if readings are reasonable (not all zeros or extreme values)
    if (abs(testX) > 10 || abs(testY) > 10 || abs(testZ) > 10) {
      Serial.println("⚠️  Warning: Accelerometer readings seem extreme");
    } else if (testX == 0 && testY == 0 && testZ == 0) {
      Serial.println("⚠️  Warning: All accelerometer readings are zero");
    } else {
      Serial.println("✓ Accelerometer readings look normal");
    }
    
  } else {
    Serial.println("Failed to read sensor ID, but I2C device detected at 0x68");
    Serial.println("Attempting to continue with accelerometer test...");
    
    // Try to read accelerometer data anyway
    mpu.accelUpdate();
    float testX = mpu.accelX();
    float testY = mpu.accelY();
    float testZ = mpu.accelZ();
    
    if (testX != 0 || testY != 0 || testZ != 0) {
      Serial.println("✓ Accelerometer is working despite ID read failure");
      Serial.print("Reading values - X: ");
      Serial.print(testX);
      Serial.print(", Y: ");
      Serial.print(testY);
      Serial.print(", Z: ");
      Serial.println(testZ);
    } else {
      Serial.println("❌ Accelerometer not responding");
      setLEDColor(255, 0, 0);  // Red for error
      while(1);  // Stop execution if sensor not working
    }
  }
  
  Serial.println("Shake detection and Grove GPS v1.1 tracking initialized!");
  Serial.println("Waiting for GPS fix...");
  Serial.println("Note: Grove GPS v1.1 may take 30-60 seconds for first fix");
  Serial.println();
  Serial.println("🔧 GPS Troubleshooting Info:");
  Serial.println("- Ensure GPS antenna has clear view of sky");
  Serial.println("- Check wiring: VCC to 5V, GND to GND, TX to pin 3, RX to pin 4");
  Serial.println("- GPS module should have blinking LED when searching for satellites");
  Serial.println("- Try different baud rates if no data is received");
  Serial.println();
  
  // Test GPS baud rates
  testGPSBaudRates();
  
  // Reset to default baud rate
  ss.begin(9600);
  Serial.println("GPS initialized at 9600 baud");
  Serial.println();
  
  // Additional GPS connection test
  Serial.println("🔍 Testing GPS connection...");
  Serial.println("If you see random characters, GPS is connected but may need time to get satellite fix");
  Serial.println("If you see nothing, check wiring and power");
  Serial.println();
  
  // Setup WiFi connection
  setupWiFi();
  Serial.println();
}

void loop() {
  // Get current time once for the entire loop
  unsigned long currentTime = millis();
  
  // Read Grove GPS v1.1 data with debugging
  while (ss.available() > 0) {
    char c = ss.read();
    gpsCharsProcessed++;
    if (gps.encode(c)) {
      if (gps.location.isValid()) {
        currentLatitude = gps.location.lat();
        currentLongitude = gps.location.lng();
        gpsLocationValid = true;
        Serial.println("✅ GPS fix acquired!");
      }
    }
  }
  
  // GPS debugging output
  if (currentTime - lastGPSDebug > GPS_DEBUG_INTERVAL) {
    Serial.println("📊 GPS Debug Info:");
    Serial.print("Characters processed: ");
    Serial.println(gpsCharsProcessed);
    Serial.print("New chars since last debug: ");
    Serial.println(gpsCharsProcessed - lastGPSCharCount);
    Serial.print("Sentences passed checksum: ");
    Serial.println(gps.passedChecksum());
    Serial.print("Sentences failed checksum: ");
    Serial.println(gps.failedChecksum());
    
    if (gpsCharsProcessed == lastGPSCharCount) {
      Serial.println("⚠️  WARNING: No GPS data received!");
      Serial.println("   Check connections and power to GPS module");
      Serial.println("   Try different baud rates: 4800, 9600, 38400");
    }
    
    lastGPSCharCount = gpsCharsProcessed;
    lastGPSDebug = currentTime;
    Serial.println("---");
  }
  
  // Read accelerometer values
  mpu.accelUpdate();
  float accelX = mpu.accelX();
  float accelY = mpu.accelY();
  float accelZ = mpu.accelZ();
  
  // Calculate total acceleration magnitude
  float accelMagnitude = sqrt(accelX * accelX + accelY * accelY + accelZ * accelZ);
  
  // Calculate change in acceleration
  float accelChange = abs(accelMagnitude - prevAccelMagnitude);
  
  // Check if shake threshold is exceeded
  if (accelChange > SHAKE_THRESHOLD) {
    // Check if enough time has passed since last shake detection (debounce)
    if (currentTime - lastShakeTime > SHAKE_DEBOUNCE) {
      // SHAKE DETECTED - Activate alerts
      alertActive = true;
      alertStartTime = currentTime;
      
      // Set LED to red and activate buzzer
      setLEDColor(255, 0, 0);  // Red
      playAlertBuzzer();
      
      // Send alert with location
      Serial.println("🚨 SHAKE ALERT! 🚨");
      Serial.print("Acceleration change: ");
      Serial.print(accelChange);
      Serial.println(" g");
      Serial.print("Total acceleration: ");
      Serial.print(accelMagnitude);
      Serial.println(" g");
      
      // Include GPS location if available
      if (gpsLocationValid) {
        Serial.print("📍 Location: ");
        Serial.print(currentLatitude, 6);
        Serial.print(", ");
        Serial.print(currentLongitude, 6);
        Serial.println();
        Serial.print("🔗 Google Maps: https://maps.google.com/?q=");
        Serial.print(currentLatitude, 6);
        Serial.print(",");
        Serial.print(currentLongitude, 6);
        Serial.println();
      } else {
        Serial.println("📍 Location: GPS fix not available");
      }
      
      Serial.println("---");
      lastShakeTime = currentTime;
    }
  }
  
  // Check if alert duration has passed
  if (alertActive && (millis() - alertStartTime > ALERT_DURATION)) {
    alertActive = false;
    // Return LED to green (ready state)
    if (gpsLocationValid) {
      setLEDColor(0, 255, 0);  // Green - GPS ready
    } else {
      setLEDColor(255, 255, 0);  // Yellow - waiting for GPS
    }
  }
  
  // Periodic GPS location updates
  if (currentTime - lastGPSUpdate > GPS_UPDATE_INTERVAL) {
    if (gpsLocationValid) {
      // Update LED to green if not in alert mode
      if (!alertActive) {
        setLEDColor(0, 255, 0);  // Green - GPS ready
      }
      
      Serial.println("📍 Current Location Update:");
      Serial.print("Latitude: ");
      Serial.print(currentLatitude, 6);
      Serial.println("°");
      Serial.print("Longitude: ");
      Serial.print(currentLongitude, 6);
      Serial.println("°");
      
      if (gps.altitude.isValid()) {
        Serial.print("Altitude: ");
        Serial.print(gps.altitude.meters());
        Serial.println(" m");
      }
      
      if (gps.speed.isValid()) {
        Serial.print("Speed: ");
        Serial.print(gps.speed.kmph());
        Serial.println(" km/h");
      }
      
      if (gps.satellites.isValid()) {
        Serial.print("Satellites: ");
        Serial.println(gps.satellites.value());
      }
      
      Serial.print("🔗 Google Maps: https://maps.google.com/?q=");
      Serial.print(currentLatitude, 6);
      Serial.print(",");
      Serial.print(currentLongitude, 6);
      Serial.println();
      Serial.println("---");
    } else {
      // Update LED to yellow if not in alert mode
      if (!alertActive) {
        setLEDColor(255, 255, 0);  // Yellow - waiting for GPS
      }
      
      Serial.println("📍 Waiting for Grove GPS v1.1 fix...");
      if (gps.charsProcessed() < 10) {
        Serial.println("⚠️  Check Grove GPS v1.1 wiring and antenna");
        Serial.println("💡 Grove GPS v1.1 requires clear sky view for optimal performance");
      }
    }
    lastGPSUpdate = currentTime;
  }
  
  // Update previous acceleration for next comparison
  prevAccelMagnitude = accelMagnitude;
  
  // Handle HTTP requests from iOS app
  handleHTTPRequests();
  
  // Small delay to avoid overwhelming the serial monitor
  delay(50);
}
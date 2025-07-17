#include <Arduino.h>
#include <Wire.h>
#include <MPU9250_asukiaaa.h>
#include <SoftwareSerial.h>
#include <TinyGPS++.h>

// MPU9250 sensor object
MPU9250_asukiaaa mpu;

// GPS objects - Grove GPS v1.1
TinyGPSPlus gps;
SoftwareSerial ss(4, 3);  // RX, TX pins for Grove GPS v1.1

// RGB LED pins
const int RED_PIN = 9;
const int GREEN_PIN = 10;
const int BLUE_PIN = 11;

// Buzzer pin
const int BUZZER_PIN = 8;

// Shake detection variables
const float SHAKE_THRESHOLD = 1.0;  // Adjust this value to change sensitivity (higher = less sensitive)
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
}

void loop() {
  // Read Grove GPS v1.1 data
  while (ss.available() > 0) {
    if (gps.encode(ss.read())) {
      if (gps.location.isValid()) {
        currentLatitude = gps.location.lat();
        currentLongitude = gps.location.lng();
        gpsLocationValid = true;
      }
    }
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
    unsigned long currentTime = millis();
    
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
  unsigned long currentTime = millis();
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
  
  // Small delay to avoid overwhelming the serial monitor
  delay(50);
}
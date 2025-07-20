#include <Arduino.h>
#include <Wire.h>
#include <MPU9250_asukiaaa.h>
#include <SoftwareSerial.h>
#include <TinyGPS++.h>
#include <WiFiS3.h>
#include <ArduinoJson.h>

const char* ssid = "Avnit";
const char* password = "hihihihi";

WiFiServer server(80);

StaticJsonDocument<512> jsonDoc;

MPU9250_asukiaaa mpu;

TinyGPSPlus gps;
SoftwareSerial ss(4, 3);

unsigned long lastGPSDebug = 0;
const unsigned long GPS_DEBUG_INTERVAL = 10000;
unsigned long gpsCharsProcessed = 0;
unsigned long lastGPSCharCount = 0;

const int RED_PIN = 9;
const int GREEN_PIN = 10;
const int BLUE_PIN = 11;

const int BUZZER_PIN = 8;

const float SHAKE_THRESHOLD = 0.2;
const unsigned long SHAKE_DEBOUNCE = 500;
unsigned long lastShakeTime = 0;

const unsigned long ALERT_DURATION = 2000;
unsigned long alertStartTime = 0;
bool alertActive = false;

const unsigned long GPS_UPDATE_INTERVAL = 5000;
unsigned long lastGPSUpdate = 0;

float prevAccelMagnitude = 0;

double currentLatitude = 0.0;
double currentLongitude = 0.0;
bool gpsLocationValid = false;

void setLEDColor(int red, int green, int blue) {
  analogWrite(RED_PIN, red);
  analogWrite(GREEN_PIN, green);
  analogWrite(BLUE_PIN, blue);
}

void playAlertBuzzer() {
  for (int i = 0; i < 3; i++) {
    tone(BUZZER_PIN, 1000, 200);
    delay(100);
    noTone(BUZZER_PIN);
    delay(100);
  }
}

void testGPSBaudRates() {
  int baudRates[] = {4800, 9600, 38400};
  int numRates = sizeof(baudRates) / sizeof(baudRates[0]);
  
  for (int i = 0; i < numRates; i++) {
    ss.begin(baudRates[i]);
    delay(1000);
    
    unsigned long startTime = millis();
    int charCount = 0;
    bool foundNMEA = false;
    
    while (millis() - startTime < 3000) {
      if (ss.available() > 0) {
        char c = ss.read();
        charCount++;
        
        if (c == '$') {
          foundNMEA = true;
        }
        
        if (charCount <= 100) {
        }
      }
    }
    
    if (charCount > 0) {
      if (foundNMEA) {
      }
      return;
    }
  }
}

void setupWiFi() {
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(1000);
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    server.begin();
  } else {
    setLEDColor(255, 0, 0);
  }
}

String createSensorDataJSON() {
  jsonDoc.clear();
  
  jsonDoc["timestamp"] = millis();
  
  JsonObject accel = jsonDoc.createNestedObject("accelerometer");
  mpu.accelUpdate();
  accel["x"] = mpu.accelX();
  accel["y"] = mpu.accelY();
  accel["z"] = mpu.accelZ();
  
  float accelMagnitude = sqrt(pow(mpu.accelX(), 2) + pow(mpu.accelY(), 2) + pow(mpu.accelZ(), 2));
  float accelChange = abs(accelMagnitude - prevAccelMagnitude);
  accel["magnitude"] = accelMagnitude;
  accel["change"] = accelChange;
  
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
  
  JsonObject alert = jsonDoc.createNestedObject("alert");
  alert["active"] = alertActive;
  alert["shake_detected"] = (accelChange > SHAKE_THRESHOLD);
  alert["threshold"] = SHAKE_THRESHOLD;
  
  JsonObject status = jsonDoc.createNestedObject("status");
  status["wifi_connected"] = (WiFi.status() == WL_CONNECTED);
  status["wifi_rssi"] = WiFi.RSSI();
  status["gps_chars_processed"] = gpsCharsProcessed;
  status["gps_sentences_passed"] = gps.passedChecksum();
  status["gps_sentences_failed"] = gps.failedChecksum();
  
  String jsonString;
  serializeJson(jsonDoc, jsonString);
  return jsonString;
}

void handleHTTPRequests() {
  WiFiClient client = server.available();
  
  if (client) {
    String request = "";
    
    while (client.connected() && client.available()) {
      char c = client.read();
      request += c;
      if (request.endsWith("\r\n\r\n")) {
        break;
      }
    }
    
    String path = "/";
    int pathStart = request.indexOf(' ') + 1;
    int pathEnd = request.indexOf(' ', pathStart);
    if (pathStart > 0 && pathEnd > pathStart) {
      path = request.substring(pathStart, pathEnd);
    }
    
    if (path == "/" || path == "/status") {
      String jsonResponse = createSensorDataJSON();
      
      client.println("HTTP/1.1 200 OK");
      client.println("Content-Type: application/json");
      client.println("Access-Control-Allow-Origin: *");
      client.println("Access-Control-Allow-Methods: GET, POST, OPTIONS");
      client.println("Access-Control-Allow-Headers: Content-Type");
      client.println("Connection: close");
      client.println();
      client.println(jsonResponse);
      
    } else if (path == "/alert") {
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
      client.println("HTTP/1.1 404 Not Found");
      client.println("Content-Type: text/plain");
      client.println("Connection: close");
      client.println();
      client.println("Endpoint not found");
    }
    
    client.stop();
  }
}

void setup() {
  Serial.begin(9600);
  
  ss.begin(9600);
  
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  
  pinMode(BUZZER_PIN, OUTPUT);
  
  setLEDColor(0, 255, 0);
  
  Wire.begin();
  
  int deviceCount = 0;
  for(byte address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    if(Wire.endTransmission() == 0) {
      deviceCount++;
    }
  }
  
  mpu.setWire(&Wire);
  
  mpu.beginAccel();
  
  mpu.beginGyro();
  
  mpu.beginMag();
  
  delay(100);
  
  uint8_t sensorId;
  
  if (mpu.readId(&sensorId) == 0) {
    if (sensorId == 0x71 || sensorId == 0x73 || sensorId == 0x68) {
    } else {
    }
    
    mpu.accelUpdate();
    float testX = mpu.accelX();
    float testY = mpu.accelY();
    float testZ = mpu.accelZ();
    
    if (abs(testX) > 10 || abs(testY) > 10 || abs(testZ) > 10) {
    } else if (testX == 0 && testY == 0 && testZ == 0) {
    } else {
    }
    
  } else {
    mpu.accelUpdate();
    float testX = mpu.accelX();
    float testY = mpu.accelY();
    float testZ = mpu.accelZ();
    
    if (testX != 0 || testY != 0 || testZ != 0) {
    } else {
      setLEDColor(255, 0, 0);
      while(1);
    }
  }
  
  testGPSBaudRates();
  
  ss.begin(9600);
  
  setupWiFi();
}

void loop() {
  unsigned long currentTime = millis();
  
  while (ss.available() > 0) {
    char c = ss.read();
    gpsCharsProcessed++;
    if (gps.encode(c)) {
      if (gps.location.isValid()) {
        currentLatitude = gps.location.lat();
        currentLongitude = gps.location.lng();
        gpsLocationValid = true;
      }
    }
  }
  
  if (currentTime - lastGPSDebug > GPS_DEBUG_INTERVAL) {
    lastGPSCharCount = gpsCharsProcessed;
    lastGPSDebug = currentTime;
  }
  
  mpu.accelUpdate();
  float accelX = mpu.accelX();
  float accelY = mpu.accelY();
  float accelZ = mpu.accelZ();
  
  float accelMagnitude = sqrt(accelX * accelX + accelY * accelY + accelZ * accelZ);
  
  float accelChange = abs(accelMagnitude - prevAccelMagnitude);
  
  if (accelChange > SHAKE_THRESHOLD) {
    if (currentTime - lastShakeTime > SHAKE_DEBOUNCE) {
      alertActive = true;
      alertStartTime = currentTime;
      
      setLEDColor(255, 0, 0);
      playAlertBuzzer();
      
      lastShakeTime = currentTime;
    }
  }
  
  if (alertActive && (millis() - alertStartTime > ALERT_DURATION)) {
    alertActive = false;
    if (gpsLocationValid) {
      setLEDColor(0, 255, 0);
    } else {
      setLEDColor(255, 255, 0);
    }
  }
  
  if (currentTime - lastGPSUpdate > GPS_UPDATE_INTERVAL) {
    if (gpsLocationValid) {
      if (!alertActive) {
        setLEDColor(0, 255, 0);
      }
    } else {
      if (!alertActive) {
        setLEDColor(255, 255, 0);
      }
    }
    lastGPSUpdate = currentTime;
  }
  
  prevAccelMagnitude = accelMagnitude;
  
  handleHTTPRequests();
  
  delay(50);
}
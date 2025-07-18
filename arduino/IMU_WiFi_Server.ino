#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <Wire.h>


const char* ssid = "Avnit";
const char* password = "hihihihi";


#define MPU6050_ADDR 0x68
#define MPU6050_ACCEL_XOUT_H 0x3B
#define MPU6050_PWR_MGMT_1 0x6B


WebServer server(80);
const int SERVER_PORT = 80;


struct IMUData {
  float ax, ay, az;
  float gx, gy, gz;
  float temp;
  bool alert;
  String alertType;
};

IMUData currentData;
unsigned long lastDataTime = 0;
const unsigned long DATA_INTERVAL = 100;


const float FALL_THRESHOLD = 20.0;
const float MOVEMENT_THRESHOLD = 5.0;
bool fallDetected = false;
bool movementDetected = false;

void setup() {
  Serial.begin(115200);
  Serial.println("GuardIt IMU WiFi Server Starting...");
  

  Wire.begin();
  

  if (!initMPU6050()) {
    Serial.println("Failed to initialize MPU6050!");
    while (1);
  }
  

  connectToWiFi();
  
  setupServerRoutes();
  
  server.begin();
  Serial.println("HTTP server started");
  
  Serial.print("Server IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("Server Port: ");
  Serial.println(SERVER_PORT);
  Serial.println("Ready to receive connections from GuardIt app!");
}

void loop() {
  server.handleClient();
  
  if (millis() - lastDataTime >= DATA_INTERVAL) {
    readIMUData();
    detectEvents();
    lastDataTime = millis();
  }
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi connection lost. Reconnecting...");
    connectToWiFi();
  }
}

bool initMPU6050() {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(MPU6050_PWR_MGMT_1);
  Wire.write(0);
  byte error = Wire.endTransmission();
  
  if (error != 0) {
    Serial.println("MPU6050 not found!");
    return false;
  }
  
  Serial.println("MPU6050 initialized successfully");
  return true;
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
  }
}

void setupServerRoutes() {
  server.on("/", HTTP_GET, []() {
    server.send(200, "application/json", getServerInfo());
  });
  
  server.on("/status", HTTP_GET, []() {
    server.send(200, "application/json", getStatusInfo());
  });
  
  server.on("/imu", HTTP_GET, []() {
    server.send(200, "application/json", getIMUDataJson());
  });
  
  server.on("/data", HTTP_GET, []() {
    server.send(200, "application/json", getIMUDataJson());
  });
  
  server.on("/sensor", HTTP_GET, []() {
    server.send(200, "application/json", getIMUDataJson());
  });
  
  server.on("/", HTTP_OPTIONS, []() {
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
    server.send(200);
  });
  
  server.onNotFound([]() {
    server.send(404, "application/json", "{\"error\": \"Endpoint not found\"}");
  });
}

String getServerInfo() {
  DynamicJsonDocument doc(512);
  doc["name"] = "GuardIt IMU Server";
  doc["version"] = "1.0.0";
  doc["ip"] = WiFi.localIP().toString();
  doc["port"] = SERVER_PORT;
  doc["status"] = "running";
  doc["endpoints"] = JsonArray();
  doc["endpoints"].add("/status");
  doc["endpoints"].add("/imu");
  doc["endpoints"].add("/data");
  doc["endpoints"].add("/sensor");
  
  String response;
  serializeJson(doc, response);
  return response;
}

String getStatusInfo() {
  DynamicJsonDocument doc(256);
  doc["connected"] = true;
  doc["ip"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  doc["uptime"] = millis() / 1000;
  doc["last_data_time"] = lastDataTime;
  
  String response;
  serializeJson(doc, response);
  return response;
}

String getIMUDataJson() {
  DynamicJsonDocument doc(512);
  doc["ax"] = currentData.ax;
  doc["ay"] = currentData.ay;
  doc["az"] = currentData.az;
  doc["gx"] = currentData.gx;
  doc["gy"] = currentData.gy;
  doc["gz"] = currentData.gz;
  doc["temp"] = currentData.temp;
  doc["alert"] = currentData.alert;
  doc["alert_type"] = currentData.alertType;
  doc["timestamp"] = millis();
  
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
  
  String response;
  serializeJson(doc, response);
  return response;
}

void readIMUData() {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(MPU6050_ACCEL_XOUT_H);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU6050_ADDR, 14, true);
  
  if (Wire.available() >= 14) {
    int16_t ax_raw = Wire.read() << 8 | Wire.read();
    int16_t ay_raw = Wire.read() << 8 | Wire.read();
    int16_t az_raw = Wire.read() << 8 | Wire.read();
    
    int16_t temp_raw = Wire.read() << 8 | Wire.read();
    
    int16_t gx_raw = Wire.read() << 8 | Wire.read();
    int16_t gy_raw = Wire.read() << 8 | Wire.read();
    int16_t gz_raw = Wire.read() << 8 | Wire.read();
    
    currentData.ax = ax_raw / 16384.0;
    currentData.ay = ay_raw / 16384.0;
    currentData.az = az_raw / 16384.0;
    currentData.temp = temp_raw / 340.0 + 36.53;
    currentData.gx = gx_raw / 131.0;
    currentData.gy = gy_raw / 131.0;
    currentData.gz = gz_raw / 131.0;
    
    static unsigned long lastDebugTime = 0;
    if (millis() - lastDebugTime > 5000) {
      Serial.printf("Raw IMU - Accel: %d, %d, %d | Gyro: %d, %d, %d | Temp: %d\n",
                    ax_raw, ay_raw, az_raw, gx_raw, gy_raw, gz_raw, temp_raw);
      lastDebugTime = millis();
    }
  } else {
    Serial.println("Warning: Not enough data from MPU6050");
  }
}

void detectEvents() {
  float accel_magnitude = sqrt(currentData.ax * currentData.ax + 
                              currentData.ay * currentData.ay + 
                              currentData.az * currentData.az);
  
  float gyro_magnitude = sqrt(currentData.gx * currentData.gx + 
                             currentData.gy * currentData.gy + 
                             currentData.gz * currentData.gz);
  
  if (accel_magnitude > FALL_THRESHOLD && !fallDetected) {
    fallDetected = true;
    currentData.alert = true;
    currentData.alertType = "fall";
    Serial.println("FALL DETECTED!");
  } else if (accel_magnitude <= FALL_THRESHOLD) {
    fallDetected = false;
  }
  
  if (gyro_magnitude > MOVEMENT_THRESHOLD && !movementDetected) {
    movementDetected = true;
    currentData.alert = true;
    currentData.alertType = "movement";
    Serial.println("UNUSUAL MOVEMENT DETECTED!");
  } else if (gyro_magnitude <= MOVEMENT_THRESHOLD) {
    movementDetected = false;
  }
  
  static unsigned long lastAlertTime = 0;
  if (currentData.alert && millis() - lastAlertTime > 5000) {
    currentData.alert = false;
    currentData.alertType = "";
    lastAlertTime = millis();
  }
  
  if (millis() % 1000 < 100) {
    Serial.printf("Accel: %.2f, %.2f, %.2f | Gyro: %.2f, %.2f, %.2f | Temp: %.1f°C\n",
                  currentData.ax, currentData.ay, currentData.az,
                  currentData.gx, currentData.gy, currentData.gz,
                  currentData.temp);
  }
} 
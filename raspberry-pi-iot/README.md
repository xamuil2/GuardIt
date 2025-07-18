# Raspberry Pi IoT Device

A comprehensive IoT solution for Raspberry Pi 4B that collects IMU data, controls hardware components, and streams camera feeds to an iOS application.

## Features

- **MPU-9250 IMU Sensor**: Real-time accelerometer, gyroscope, and magnetometer data collection via I2C
- **Hardware Control**: RGB LED and passive buzzer control via GPIO
- **Dual Camera Streaming**: Support for both CSI camera module and USB webcam
- **iOS App Integration**: RESTful API and WebSocket endpoints for real-time communication
- **Asynchronous Design**: Non-blocking operations for optimal performance

## Hardware Requirements

- Raspberry Pi 4B
- MPU-9250 IMU sensor module
- RGB LED (common cathode or anode)
- Passive buzzer
- CSI camera module
- USB webcam
- Jumper wires and breadboard

## Pin Configuration

### MPU-9250 (I2C)
- VCC → 3.3V
- GND → Ground
- SDA → GPIO 2 (Pin 3)
- SCL → GPIO 3 (Pin 5)

### RGB LED
- Red → GPIO 18 (Pin 12)
- Green → GPIO 19 (Pin 35)
- Blue → GPIO 20 (Pin 38)
- Common → Ground (for common cathode)

### Passive Buzzer
- Positive → GPIO 21 (Pin 40)
- Negative → Ground

## Installation

1. **Enable I2C and Camera**:
   ```bash
   sudo raspi-config
   # Navigate to Interfacing Options → I2C → Enable
   # Navigate to Interfacing Options → Camera → Enable
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install system dependencies**:
   ```bash
   sudo apt update
   sudo apt install -y python3-smbus i2c-tools
   ```

## Usage

1. **Start the IoT server**:
   ```bash
   python main.py
   ```

2. **Access the API**:
   - Web interface: http://your-pi-ip:8000
   - API documentation: http://your-pi-ip:8000/docs
   - WebSocket endpoint: ws://your-pi-ip:8000/ws

## API Endpoints

### REST API
- `GET /`: Health check and system status
- `GET /imu`: Get current IMU readings
- `POST /led`: Control RGB LED (color and brightness)
- `POST /buzzer`: Control buzzer (frequency and duration)
- `GET /camera/csi/stream`: CSI camera video stream
- `GET /camera/usb/stream`: USB camera video stream

### WebSocket
- `/ws`: Real-time sensor data and system events

## iOS App Integration

The server provides endpoints optimized for iOS app consumption:
- JSON responses for easy parsing
- WebSocket for real-time updates
- MJPEG streams for camera feeds
- RESTful design following iOS networking best practices

## Configuration

Edit `config.py` to customize:
- GPIO pin assignments
- I2C addresses
- Camera settings
- Network configuration
- Sensor sampling rates

## Development

Run in development mode with auto-reload:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## License

MIT License

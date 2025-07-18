# Configuration settings for the IoT device

# GPIO Pin Configuration
class GPIOConfig:
    # RGB LED pins (PWM capable pins recommended)
    LED_RED_PIN = 18
    LED_GREEN_PIN = 19
    LED_BLUE_PIN = 20
    
    # Buzzer pin
    BUZZER_PIN = 21
    
    # I2C configuration (default Raspberry Pi I2C pins)
    I2C_SDA_PIN = 2  # GPIO 2
    I2C_SCL_PIN = 3  # GPIO 3

# I2C Configuration
class I2CConfig:
    BUS_NUMBER = 1  # I2C bus 1 (default on Raspberry Pi)
    MPU9250_ADDRESS = 0x68  # Default MPU-9250 I2C address

# Camera Configuration
class CameraConfig:
    CSI_CAMERA_INDEX = 0
    USB_CAMERA_INDEX = 1
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    FPS = 30
    QUALITY = 80  # JPEG quality for streaming

# Server Configuration
class ServerConfig:
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = True
    
# Sensor Configuration
class SensorConfig:
    IMU_SAMPLE_RATE = 50  # Hz
    GYRO_RANGE = 2000     # degrees/second
    ACCEL_RANGE = 16      # g
    
# WebSocket Configuration
class WebSocketConfig:
    PING_INTERVAL = 30    # seconds
    PING_TIMEOUT = 10     # seconds
    MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB

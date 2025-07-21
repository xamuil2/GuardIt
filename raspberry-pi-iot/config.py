class GPIOConfig:
    LED_RED_PIN = 18
    LED_GREEN_PIN = 19
    LED_BLUE_PIN = 20
    
    BUZZER_PIN = 21
    
    I2C_SDA_PIN = 2
    I2C_SCL_PIN = 3

class I2CConfig:
    BUS_NUMBER = 1
    MPU9250_ADDRESS = 0x68

class CameraConfig:
    CSI_CAMERA_INDEX = 0
    USB_CAMERA_INDEX = 1
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    FPS = 30
    QUALITY = 80

class ServerConfig:
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = True
    
class SensorConfig:
    IMU_SAMPLE_RATE = 50
    GYRO_RANGE = 2000
    ACCEL_RANGE = 16
    
class WebSocketConfig:
    PING_INTERVAL = 30
    PING_TIMEOUT = 10
    MAX_MESSAGE_SIZE = 1024 * 1024

import RPi.GPIO as GPIO
import smbus2
import time
import math
import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Tuple
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HardwareConfig:
    LED_RED_PIN = 18
    LED_GREEN_PIN = 19  
    LED_BLUE_PIN = 20
    
    BUZZER_PIN = 21
    
    I2C_BUS = 1
    MPU6050_ADDR = 0x68
    MPU9250_ADDR = 0x68
    
    FALL_THRESHOLD = 15.0
    MOVEMENT_THRESHOLD = 2.0
    DATA_INTERVAL = 0.1

@dataclass
class IMUData:
    
    ax: float = 0.0
    ay: float = 0.0
    az: float = 0.0
    gx: float = 0.0
    gy: float = 0.0
    gz: float = 0.0
    temp: float = 0.0
    alert: bool = False
    alert_type: str = ""
    timestamp: float = 0.0

class GuardItHardware:

    def __init__(self):
        self.bus = None
        self.led_pwm = {}
        self.buzzer_pwm = None
        self.current_data = IMUData()
        self.running = False
        
        self.fall_detected = False
        self.movement_detected = False
        self.last_alert_time = 0
        
        self.init_gpio()
        self.init_i2c()
    
    def init_gpio(self):
        
        logger.info("🔧 Initializing GPIO...")
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        GPIO.setup(HardwareConfig.LED_RED_PIN, GPIO.OUT)
        GPIO.setup(HardwareConfig.LED_GREEN_PIN, GPIO.OUT)
        GPIO.setup(HardwareConfig.LED_BLUE_PIN, GPIO.OUT)
        GPIO.setup(HardwareConfig.BUZZER_PIN, GPIO.OUT)
        
        self.led_pwm['red'] = GPIO.PWM(HardwareConfig.LED_RED_PIN, 1000)
        self.led_pwm['green'] = GPIO.PWM(HardwareConfig.LED_GREEN_PIN, 1000)
        self.led_pwm['blue'] = GPIO.PWM(HardwareConfig.LED_BLUE_PIN, 1000)
        self.buzzer_pwm = GPIO.PWM(HardwareConfig.BUZZER_PIN, 1000)
        
        for pwm in self.led_pwm.values():
            pwm.start(0)
        self.buzzer_pwm.start(0)
        
        logger.info("✅ GPIO initialized successfully")
    
    def init_i2c(self):
        
        try:
            self.bus = smbus2.SMBus(HardwareConfig.I2C_BUS)
            logger.info("✅ I2C bus initialized")
        except Exception as e:
            logger.error(f"❌ I2C initialization failed: {e}")
    
    def detect_imu_sensor(self) -> Tuple[bool, str]:
        
        logger.info("🔍 Detecting IMU sensor...")
        
        for addr, name in [(0x68, "MPU6050/MPU9250"), (0x69, "MPU6050/MPU9250 (alt)")]:
            try:
                who_am_i = self.bus.read_byte_data(addr, 0x75)
                logger.info(f"   Device at 0x{addr:02X}: WHO_AM_I = 0x{who_am_i:02X}")
                
                if who_am_i in [0x68, 0x70, 0x71, 0x73]:
                    HardwareConfig.MPU6050_ADDR = addr
                    sensor_map = {0x68: "MPU6050", 0x70: "MPU6500", 0x71: "MPU9250", 0x73: "MPU9255"}
                    sensor_type = sensor_map.get(who_am_i, f"Unknown (0x{who_am_i:02X})")
                    logger.info(f"✅ Detected {sensor_type} at address 0x{addr:02X}")
                    return True, sensor_type
                    
            except Exception as e:
                logger.debug(f"   No device at 0x{addr:02X}: {e}")
        
        logger.warning("❌ No IMU sensor detected")
        return False, "None"
    
    def init_mpu6050(self) -> bool:
        
        logger.info("🎯 Initializing IMU sensor...")
        
        try:
            self.bus.write_byte_data(HardwareConfig.MPU6050_ADDR, 0x6B, 0)
            time.sleep(0.1)
            
            self.bus.write_byte_data(HardwareConfig.MPU6050_ADDR, 0x1B, 0x18)
            self.bus.write_byte_data(HardwareConfig.MPU6050_ADDR, 0x1C, 0x18)
            time.sleep(0.1)
            
            logger.info("✅ IMU sensor initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ IMU initialization failed: {e}")
            return False
    
    def read_imu_data(self):
        
        try:
            data = self.bus.read_i2c_block_data(HardwareConfig.MPU6050_ADDR, 0x3B, 14)
            
            ax_raw = (data[0] << 8) | data[1]
            ay_raw = (data[2] << 8) | data[3]
            az_raw = (data[4] << 8) | data[5]
            temp_raw = (data[6] << 8) | data[7]
            gx_raw = (data[8] << 8) | data[9]
            gy_raw = (data[10] << 8) | data[11]
            gz_raw = (data[12] << 8) | data[13]
            
            if ax_raw > 32767: ax_raw -= 65536
            if ay_raw > 32767: ay_raw -= 65536
            if az_raw > 32767: az_raw -= 65536
            if temp_raw > 32767: temp_raw -= 65536
            if gx_raw > 32767: gx_raw -= 65536
            if gy_raw > 32767: gy_raw -= 65536
            if gz_raw > 32767: gz_raw -= 65536
            
            self.current_data.ax = ax_raw / 16384.0
            self.current_data.ay = ay_raw / 16384.0
            self.current_data.az = az_raw / 16384.0
            self.current_data.temp = temp_raw / 340.0 + 36.53
            self.current_data.gx = gx_raw / 131.0
            self.current_data.gy = gy_raw / 131.0
            self.current_data.gz = gz_raw / 131.0
            self.current_data.timestamp = time.time()
            
        except Exception as e:
            logger.warning(f"IMU read error: {e}")
    
    def detect_events(self):
        
        accel_magnitude = math.sqrt(
            self.current_data.ax ** 2 + 
            self.current_data.ay ** 2 + 
            self.current_data.az ** 2
        )
        
        gyro_magnitude = math.sqrt(
            self.current_data.gx ** 2 + 
            self.current_data.gy ** 2 + 
            self.current_data.gz ** 2
        )
        
        if accel_magnitude > HardwareConfig.FALL_THRESHOLD and not self.fall_detected:
            self.fall_detected = True
            self.current_data.alert = True
            self.current_data.alert_type = "fall"
            logger.warning("🚨 FALL DETECTED!")
            self.trigger_alert_sequence("fall")
        elif accel_magnitude <= HardwareConfig.FALL_THRESHOLD:
            self.fall_detected = False
        
        if gyro_magnitude > HardwareConfig.MOVEMENT_THRESHOLD and not self.movement_detected:
            self.movement_detected = True
            self.current_data.alert = True
            self.current_data.alert_type = "movement"
            logger.warning("🚨 UNUSUAL MOVEMENT DETECTED!")
            self.trigger_alert_sequence("movement")
        elif gyro_magnitude <= HardwareConfig.MOVEMENT_THRESHOLD:
            self.movement_detected = False
        
        current_time = time.time()
        if self.current_data.alert and (current_time - self.last_alert_time) > 5.0:
            self.current_data.alert = False
            self.current_data.alert_type = ""
            self.clear_alert_sequence()
    
    def trigger_alert_sequence(self, alert_type: str):
        
        if alert_type == "fall":
            self.set_led_color(255, 0, 0)
            self.buzz_tone(2000, 1.0)
        elif alert_type == "movement":
            self.set_led_color(255, 255, 0)
            self.buzz_tone(1500, 0.5)
        
        self.last_alert_time = time.time()
    
    def clear_alert_sequence(self):
        
        self.set_led_color(0, 255, 0)
        time.sleep(1)
        self.set_led_color(0, 0, 0)
    
    def set_led_color(self, red: int, green: int, blue: int):
        
        try:
            red_duty = (red / 255.0) * 100
            green_duty = (green / 255.0) * 100
            blue_duty = (blue / 255.0) * 100
            
            self.led_pwm['red'].ChangeDutyCycle(red_duty)
            self.led_pwm['green'].ChangeDutyCycle(green_duty)
            self.led_pwm['blue'].ChangeDutyCycle(blue_duty)
            
        except Exception as e:
            logger.error(f"LED control error: {e}")
    
    def buzz_tone(self, frequency: int, duration: float):
        
        try:
            self.buzzer_pwm.ChangeFrequency(frequency)
            self.buzzer_pwm.ChangeDutyCycle(90)
            time.sleep(duration)
            self.buzzer_pwm.ChangeDutyCycle(0)
        except Exception as e:
            logger.error(f"Buzzer control error: {e}")
    
    def get_status_json(self) -> str:
        
        data = {
            "ax": round(self.current_data.ax, 3),
            "ay": round(self.current_data.ay, 3),
            "az": round(self.current_data.az, 3),
            "gx": round(self.current_data.gx, 3),
            "gy": round(self.current_data.gy, 3),
            "gz": round(self.current_data.gz, 3),
            "temp": round(self.current_data.temp, 1),
            "alert": self.current_data.alert,
            "alert_type": self.current_data.alert_type,
            "timestamp": int(self.current_data.timestamp * 1000)
        }
        return json.dumps(data, indent=2)
    
    def test_leds(self):
        
        logger.info("🌈 Testing RGB LEDs...")
        
        colors = [
            (255, 0, 0, "Red"),
            (0, 255, 0, "Green"), 
            (0, 0, 255, "Blue"),
            (255, 255, 0, "Yellow"),
            (255, 0, 255, "Magenta"),
            (0, 255, 255, "Cyan"),
            (255, 255, 255, "White")
        ]
        
        for r, g, b, name in colors:
            logger.info(f"   Testing {name} LED...")
            self.set_led_color(r, g, b)
            time.sleep(1)
        
        self.set_led_color(0, 0, 0)
        logger.info("✅ LED test completed")
    
    def test_buzzer(self):
        
        logger.info("🔊 Testing SUPER LOUD buzzer...")
        
        frequencies = [500, 1000, 1500, 2000, 2500]
        for freq in frequencies:
            logger.info(f"   Testing {freq}Hz LOUD tone...")
            self.buzz_tone(freq, 0.8)
            time.sleep(0.3)
        
        logger.info("✅ LOUD buzzer test completed")
    
    def demo_alert_detection(self, duration: float = 20):
        
        logger.info(f"🚨 STARTING SUPER LOUD ALERT DEMO for {duration} seconds...")
        logger.info("🎯 Move, shake, or tilt the device to trigger LOUD alerts!")
        
        demo_fall_threshold = 8.0
        demo_movement_threshold = 1.0
        
        start_time = time.time()
        last_data_time = 0
        alert_count = 0
        
        while time.time() - start_time < duration:
            current_time = time.time()
            
            if current_time - last_data_time >= HardwareConfig.DATA_INTERVAL:
                self.read_imu_data()
                
                accel_magnitude = math.sqrt(
                    self.current_data.ax ** 2 + 
                    self.current_data.ay ** 2 + 
                    self.current_data.az ** 2
                )
                
                gyro_magnitude = math.sqrt(
                    self.current_data.gx ** 2 + 
                    self.current_data.gy ** 2 + 
                    self.current_data.gz ** 2
                )
                
                if accel_magnitude > demo_fall_threshold:
                    alert_count += 1
                    logger.warning(f"🚨 DEMO FALL #{alert_count} DETECTED! (Magnitude: {accel_magnitude:.2f})")
                    self.set_led_color(255, 0, 0)
                    self.buzz_tone(2500, 1.2)
                    time.sleep(0.5)
                
                elif gyro_magnitude > demo_movement_threshold:
                    alert_count += 1
                    logger.warning(f"🚨 DEMO MOVEMENT #{alert_count} DETECTED! (Magnitude: {gyro_magnitude:.2f})")
                    self.set_led_color(255, 255, 0)
                    self.buzz_tone(2000, 0.8)
                    time.sleep(0.3)
                
                last_data_time = current_time
                
                if int(current_time) % 2 == 0 and (current_time - int(current_time)) < 0.2:
                    logger.info(f"📊 Accel: {accel_magnitude:.2f} | Gyro: {gyro_magnitude:.2f} | Alerts: {alert_count}")
            
            time.sleep(0.01)
        
        self.set_led_color(0, 0, 0)
        logger.info(f"✅ LOUD alert demo completed! Total alerts triggered: {alert_count}")
        
        if alert_count > 0:
            logger.info("🎉 Your alert system is SUPER responsive and LOUD!")
        else:
            logger.info("💡 Try moving the device more to trigger alerts next time!")
        
        logger.info(f"🔄 Starting monitoring loop for {duration} seconds...")
        
        start_time = time.time()
        last_data_time = 0
        
        while time.time() - start_time < duration:
            current_time = time.time()
            
            if current_time - last_data_time >= HardwareConfig.DATA_INTERVAL:
                self.read_imu_data()
                self.detect_events()
                last_data_time = current_time
                
                if int(current_time) % 1 == 0 and (current_time - int(current_time)) < 0.1:
                    logger.info(f"IMU: Accel({self.current_data.ax:.2f}, {self.current_data.ay:.2f}, {self.current_data.az:.2f}) "
                              f"Gyro({self.current_data.gx:.2f}, {self.current_data.gy:.2f}, {self.current_data.gz:.2f}) "
                              f"Temp: {self.current_data.temp:.1f}°C")
            
            time.sleep(0.01)
        
        logger.info("✅ Monitoring loop completed")
    
    def cleanup(self):
        
        logger.info("🧹 Cleaning up GPIO...")
        
        self.set_led_color(0, 0, 0)
        self.buzzer_pwm.ChangeDutyCycle(0)
        
        for pwm in self.led_pwm.values():
            pwm.stop()
        self.buzzer_pwm.stop()
        
        GPIO.cleanup()
        
        if self.bus:
            self.bus.close()
        
        logger.info("✅ Cleanup completed")

def main():

    hardware = GuardItHardware()
    
    try:
        sensor_detected, sensor_type = hardware.detect_imu_sensor()
        
        if sensor_detected:
            
            if hardware.init_mpu6050():
                
                hardware.test_leds()
                
                hardware.test_buzzer()
                
                time.sleep(3)
                hardware.demo_alert_detection(20)

            else:
        else:
            hardware.test_leds()
            hardware.test_buzzer()
    
    except KeyboardInterrupt:
    except Exception as e:
    finally:
        hardware.cleanup()

if __name__ == "__main__":
    main()

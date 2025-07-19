#!/usr/bin/env python3
"""
GuardIt Hardware Test Script
Tests RGB LED, buzzer, and MPU9250/MPU6050 IMU sensor
Mirrors the Arduino IMU_WiFi_Server.ino logic for Raspberry Pi
"""

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hardware Configuration (matching your config.py)
class HardwareConfig:
    # RGB LED pins (PWM capable)
    LED_RED_PIN = 18
    LED_GREEN_PIN = 19  
    LED_BLUE_PIN = 20
    
    # Buzzer pin
    BUZZER_PIN = 21
    
    # I2C configuration
    I2C_BUS = 1
    MPU6050_ADDR = 0x68  # Same as Arduino
    MPU9250_ADDR = 0x68  # Alternative address
    
    # IMU thresholds (adjusted for easier demo)
    FALL_THRESHOLD = 15.0      # Slightly lower for easier demo
    MOVEMENT_THRESHOLD = 2.0   # Much lower for easier trigger
    DATA_INTERVAL = 0.1  # 100ms like Arduino

@dataclass
class IMUData:
    """IMU data structure matching Arduino"""
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
    """Main hardware controller for GuardIt IoT device"""
    
    def __init__(self):
        self.bus = None
        self.led_pwm = {}
        self.buzzer_pwm = None
        self.current_data = IMUData()
        self.running = False
        
        # Alert states (matching Arduino logic)
        self.fall_detected = False
        self.movement_detected = False
        self.last_alert_time = 0
        
        # Initialize hardware
        self.init_gpio()
        self.init_i2c()
    
    def init_gpio(self):
        """Initialize GPIO for LEDs and buzzer"""
        logger.info("🔧 Initializing GPIO...")
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup LED pins
        GPIO.setup(HardwareConfig.LED_RED_PIN, GPIO.OUT)
        GPIO.setup(HardwareConfig.LED_GREEN_PIN, GPIO.OUT)
        GPIO.setup(HardwareConfig.LED_BLUE_PIN, GPIO.OUT)
        GPIO.setup(HardwareConfig.BUZZER_PIN, GPIO.OUT)
        
        # Initialize PWM (1000Hz like typical Arduino PWM)
        self.led_pwm['red'] = GPIO.PWM(HardwareConfig.LED_RED_PIN, 1000)
        self.led_pwm['green'] = GPIO.PWM(HardwareConfig.LED_GREEN_PIN, 1000)
        self.led_pwm['blue'] = GPIO.PWM(HardwareConfig.LED_BLUE_PIN, 1000)
        self.buzzer_pwm = GPIO.PWM(HardwareConfig.BUZZER_PIN, 1000)
        
        # Start all PWM with 0% duty cycle
        for pwm in self.led_pwm.values():
            pwm.start(0)
        self.buzzer_pwm.start(0)
        
        logger.info("✅ GPIO initialized successfully")
    
    def init_i2c(self):
        """Initialize I2C bus"""
        try:
            self.bus = smbus2.SMBus(HardwareConfig.I2C_BUS)
            logger.info("✅ I2C bus initialized")
        except Exception as e:
            logger.error(f"❌ I2C initialization failed: {e}")
    
    def detect_imu_sensor(self) -> Tuple[bool, str]:
        """Detect which IMU sensor is connected"""
        logger.info("🔍 Detecting IMU sensor...")
        
        # Try MPU6050/MPU9250 addresses
        for addr, name in [(0x68, "MPU6050/MPU9250"), (0x69, "MPU6050/MPU9250 (alt)")]:
            try:
                # Try to read WHO_AM_I register
                who_am_i = self.bus.read_byte_data(addr, 0x75)
                logger.info(f"   Device at 0x{addr:02X}: WHO_AM_I = 0x{who_am_i:02X}")
                
                if who_am_i in [0x68, 0x70, 0x71, 0x73]:  # MPU6050, MPU6500, MPU9250, MPU9255
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
        """Initialize MPU6050/MPU9250 sensor (matching Arduino logic)"""
        logger.info("🎯 Initializing IMU sensor...")
        
        try:
            # Wake up the MPU6050 (same as Arduino)
            self.bus.write_byte_data(HardwareConfig.MPU6050_ADDR, 0x6B, 0)
            time.sleep(0.1)
            
            # Set gyro and accel ranges
            self.bus.write_byte_data(HardwareConfig.MPU6050_ADDR, 0x1B, 0x18)  # ±2000°/s
            self.bus.write_byte_data(HardwareConfig.MPU6050_ADDR, 0x1C, 0x18)  # ±16g
            time.sleep(0.1)
            
            logger.info("✅ IMU sensor initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ IMU initialization failed: {e}")
            return False
    
    def read_imu_data(self):
        """Read IMU data (exactly matching Arduino logic)"""
        try:
            # Read 14 bytes starting from ACCEL_XOUT_H (same as Arduino)
            data = self.bus.read_i2c_block_data(HardwareConfig.MPU6050_ADDR, 0x3B, 14)
            
            # Parse raw data (same conversion as Arduino)
            ax_raw = (data[0] << 8) | data[1]
            ay_raw = (data[2] << 8) | data[3]
            az_raw = (data[4] << 8) | data[5]
            temp_raw = (data[6] << 8) | data[7]
            gx_raw = (data[8] << 8) | data[9]
            gy_raw = (data[10] << 8) | data[11]
            gz_raw = (data[12] << 8) | data[13]
            
            # Convert to signed integers
            if ax_raw > 32767: ax_raw -= 65536
            if ay_raw > 32767: ay_raw -= 65536
            if az_raw > 32767: az_raw -= 65536
            if temp_raw > 32767: temp_raw -= 65536
            if gx_raw > 32767: gx_raw -= 65536
            if gy_raw > 32767: gy_raw -= 65536
            if gz_raw > 32767: gz_raw -= 65536
            
            # Scale values (exactly matching Arduino)
            self.current_data.ax = ax_raw / 16384.0  # ±2g range
            self.current_data.ay = ay_raw / 16384.0
            self.current_data.az = az_raw / 16384.0
            self.current_data.temp = temp_raw / 340.0 + 36.53
            self.current_data.gx = gx_raw / 131.0    # ±250°/s range
            self.current_data.gy = gy_raw / 131.0
            self.current_data.gz = gz_raw / 131.0
            self.current_data.timestamp = time.time()
            
        except Exception as e:
            logger.warning(f"IMU read error: {e}")
    
    def detect_events(self):
        """Detect fall and movement events (exactly matching Arduino logic)"""
        # Calculate magnitudes (same as Arduino)
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
        
        # Fall detection (same logic as Arduino)
        if accel_magnitude > HardwareConfig.FALL_THRESHOLD and not self.fall_detected:
            self.fall_detected = True
            self.current_data.alert = True
            self.current_data.alert_type = "fall"
            logger.warning("🚨 FALL DETECTED!")
            self.trigger_alert_sequence("fall")
        elif accel_magnitude <= HardwareConfig.FALL_THRESHOLD:
            self.fall_detected = False
        
        # Movement detection (same logic as Arduino)
        if gyro_magnitude > HardwareConfig.MOVEMENT_THRESHOLD and not self.movement_detected:
            self.movement_detected = True
            self.current_data.alert = True
            self.current_data.alert_type = "movement"
            logger.warning("🚨 UNUSUAL MOVEMENT DETECTED!")
            self.trigger_alert_sequence("movement")
        elif gyro_magnitude <= HardwareConfig.MOVEMENT_THRESHOLD:
            self.movement_detected = False
        
        # Clear alerts after 5 seconds (same as Arduino)
        current_time = time.time()
        if self.current_data.alert and (current_time - self.last_alert_time) > 5.0:
            self.current_data.alert = False
            self.current_data.alert_type = ""
            self.clear_alert_sequence()
    
    def trigger_alert_sequence(self, alert_type: str):
        """Trigger LED and buzzer alert sequence - SUPER LOUD VERSION"""
        if alert_type == "fall":
            # Red flashing for fall with LOUD alarm
            self.set_led_color(255, 0, 0)  # Red
            self.buzz_tone(2000, 1.0)  # 2kHz LOUD for 1 second!
        elif alert_type == "movement":
            # Yellow flashing for movement with LOUD beep
            self.set_led_color(255, 255, 0)  # Yellow
            self.buzz_tone(1500, 0.5)  # 1.5kHz LOUD for 500ms!
        
        self.last_alert_time = time.time()
    
    def clear_alert_sequence(self):
        """Clear alert LED and buzzer"""
        self.set_led_color(0, 255, 0)  # Green for normal
        time.sleep(1)
        self.set_led_color(0, 0, 0)    # Off
    
    def set_led_color(self, red: int, green: int, blue: int):
        """Set RGB LED color (0-255 for each channel)"""
        try:
            # Convert 0-255 to 0-100 for PWM duty cycle
            red_duty = (red / 255.0) * 100
            green_duty = (green / 255.0) * 100
            blue_duty = (blue / 255.0) * 100
            
            self.led_pwm['red'].ChangeDutyCycle(red_duty)
            self.led_pwm['green'].ChangeDutyCycle(green_duty)
            self.led_pwm['blue'].ChangeDutyCycle(blue_duty)
            
        except Exception as e:
            logger.error(f"LED control error: {e}")
    
    def buzz_tone(self, frequency: int, duration: float):
        """Play buzzer tone - SUPER LOUD VERSION"""
        try:
            self.buzzer_pwm.ChangeFrequency(frequency)
            self.buzzer_pwm.ChangeDutyCycle(90)  # 90% duty cycle for MAXIMUM VOLUME!
            time.sleep(duration)
            self.buzzer_pwm.ChangeDutyCycle(0)   # Turn off
        except Exception as e:
            logger.error(f"Buzzer control error: {e}")
    
    def get_status_json(self) -> str:
        """Get current status as JSON (matching Arduino format)"""
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
            "timestamp": int(self.current_data.timestamp * 1000)  # milliseconds like Arduino
        }
        return json.dumps(data, indent=2)
    
    def test_leds(self):
        """Test RGB LED functionality"""
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
        
        self.set_led_color(0, 0, 0)  # Turn off
        logger.info("✅ LED test completed")
    
    def test_buzzer(self):
        """Test buzzer functionality - SUPER LOUD VERSION"""
        logger.info("🔊 Testing SUPER LOUD buzzer...")
        
        # Test different frequencies with maximum volume
        frequencies = [500, 1000, 1500, 2000, 2500]
        for freq in frequencies:
            logger.info(f"   Testing {freq}Hz LOUD tone...")
            self.buzz_tone(freq, 0.8)  # Longer, louder tones
            time.sleep(0.3)
        
        logger.info("✅ LOUD buzzer test completed")
    
    def demo_alert_detection(self, duration: float = 20):
        """Special demo for alert detection with SUPER LOUD buzzer"""
        logger.info(f"🚨 STARTING SUPER LOUD ALERT DEMO for {duration} seconds...")
        logger.info("🎯 Move, shake, or tilt the device to trigger LOUD alerts!")
        
        # Extra sensitive thresholds for demo
        demo_fall_threshold = 8.0      # Very low for easy demo
        demo_movement_threshold = 1.0  # Very low for easy trigger
        
        start_time = time.time()
        last_data_time = 0
        alert_count = 0
        
        while time.time() - start_time < duration:
            current_time = time.time()
            
            # Read data every DATA_INTERVAL
            if current_time - last_data_time >= HardwareConfig.DATA_INTERVAL:
                self.read_imu_data()
                
                # Calculate magnitudes with demo thresholds
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
                
                # Demo fall detection (extra sensitive)
                if accel_magnitude > demo_fall_threshold:
                    alert_count += 1
                    logger.warning(f"🚨 DEMO FALL #{alert_count} DETECTED! (Magnitude: {accel_magnitude:.2f})")
                    self.set_led_color(255, 0, 0)  # Red
                    self.buzz_tone(2500, 1.2)  # SUPER LOUD 2.5kHz for 1.2 seconds!
                    time.sleep(0.5)
                
                # Demo movement detection (extra sensitive)
                elif gyro_magnitude > demo_movement_threshold:
                    alert_count += 1
                    logger.warning(f"🚨 DEMO MOVEMENT #{alert_count} DETECTED! (Magnitude: {gyro_magnitude:.2f})")
                    self.set_led_color(255, 255, 0)  # Yellow
                    self.buzz_tone(2000, 0.8)  # SUPER LOUD 2kHz for 800ms!
                    time.sleep(0.3)
                
                last_data_time = current_time
                
                # Print data every 2 seconds
                if int(current_time) % 2 == 0 and (current_time - int(current_time)) < 0.2:
                    logger.info(f"📊 Accel: {accel_magnitude:.2f} | Gyro: {gyro_magnitude:.2f} | Alerts: {alert_count}")
            
            time.sleep(0.01)
        
        # Clear LED
        self.set_led_color(0, 0, 0)
        logger.info(f"✅ LOUD alert demo completed! Total alerts triggered: {alert_count}")
        
        if alert_count > 0:
            logger.info("🎉 Your alert system is SUPER responsive and LOUD!")
        else:
            logger.info("💡 Try moving the device more to trigger alerts next time!")
        """Run IMU monitoring loop (like Arduino main loop)"""
        logger.info(f"🔄 Starting monitoring loop for {duration} seconds...")
        
        start_time = time.time()
        last_data_time = 0
        
        while time.time() - start_time < duration:
            current_time = time.time()
            
            # Read data every DATA_INTERVAL (like Arduino)
            if current_time - last_data_time >= HardwareConfig.DATA_INTERVAL:
                self.read_imu_data()
                self.detect_events()
                last_data_time = current_time
                
                # Print data every second (like Arduino)
                if int(current_time) % 1 == 0 and (current_time - int(current_time)) < 0.1:
                    logger.info(f"IMU: Accel({self.current_data.ax:.2f}, {self.current_data.ay:.2f}, {self.current_data.az:.2f}) "
                              f"Gyro({self.current_data.gx:.2f}, {self.current_data.gy:.2f}, {self.current_data.gz:.2f}) "
                              f"Temp: {self.current_data.temp:.1f}°C")
            
            time.sleep(0.01)  # Small delay
        
        logger.info("✅ Monitoring loop completed")
    
    def cleanup(self):
        """Clean up GPIO resources"""
        logger.info("🧹 Cleaning up GPIO...")
        
        # Turn off all LEDs and buzzer
        self.set_led_color(0, 0, 0)
        self.buzzer_pwm.ChangeDutyCycle(0)
        
        # Stop PWM
        for pwm in self.led_pwm.values():
            pwm.stop()
        self.buzzer_pwm.stop()
        
        # Clean up GPIO
        GPIO.cleanup()
        
        if self.bus:
            self.bus.close()
        
        logger.info("✅ Cleanup completed")

def main():
    """Main test function"""
    print("🚀 GuardIt Hardware Test - Raspberry Pi Edition")
    print("=" * 60)
    
    hardware = GuardItHardware()
    
    try:
        # Test sequence
        print("\n1. Detecting IMU Sensor...")
        sensor_detected, sensor_type = hardware.detect_imu_sensor()
        
        if sensor_detected:
            print(f"✅ Found {sensor_type} sensor")
            
            if hardware.init_mpu6050():
                print("✅ IMU initialized successfully")
                
                print("\n2. Testing LEDs...")
                hardware.test_leds()
                
                print("\n3. Testing SUPER LOUD Buzzer...")
                hardware.test_buzzer()
                
                print("\n4. 🚨 SUPER LOUD Alert Detection Demo (20 seconds)...")
                print("   🎯 MOVE, SHAKE, or TILT the device NOW!")
                print("   🔊 WARNING: BUZZER WILL BE VERY LOUD!")
                time.sleep(3)  # Give user time to prepare
                hardware.demo_alert_detection(20)
                
                print("\n5. Final status:")
                print(hardware.get_status_json())
                
            else:
                print("❌ Failed to initialize IMU")
        else:
            print("❌ No IMU sensor detected - check I2C connections")
            print("\n🔧 Testing LEDs and buzzer only...")
            hardware.test_leds()
            hardware.test_buzzer()
    
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
    finally:
        hardware.cleanup()

if __name__ == "__main__":
    main()

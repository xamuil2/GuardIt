#!/usr/bin/env python3
"""
Quick IMU Sensor Identification and Test
"""

import smbus2
import time

def identify_imu_sensor():
    """Identify the exact IMU sensor"""
    print("🔍 Identifying IMU Sensor...")
    
    bus = smbus2.SMBus(1)
    
    try:
        # Read WHO_AM_I register
        who_am_i = bus.read_byte_data(0x68, 0x75)
        print(f"WHO_AM_I: 0x{who_am_i:02X}")
        
        # Identify sensor based on WHO_AM_I
        sensor_map = {
            0x68: "MPU6050",
            0x70: "MPU6500", 
            0x71: "MPU9250",
            0x73: "MPU9255"
        }
        
        sensor_name = sensor_map.get(who_am_i, f"Unknown (0x{who_am_i:02X})")
        print(f"Detected sensor: {sensor_name}")
        
        if who_am_i in [0x68, 0x70, 0x71, 0x73]:
            print("✅ This is a compatible MPU-series sensor!")
            test_sensor_basic(bus)
        else:
            print("❌ Unknown sensor type")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        bus.close()

def test_sensor_basic(bus):
    """Basic sensor functionality test"""
    print("\n🧪 Testing sensor functionality...")
    
    try:
        # Wake up sensor
        bus.write_byte_data(0x68, 0x6B, 0)
        time.sleep(0.1)
        print("✅ Sensor woken up")
        
        # Read some data
        data = bus.read_i2c_block_data(0x68, 0x3B, 6)  # Read accel data
        
        # Convert to signed values
        ax = ((data[0] << 8) | data[1])
        ay = ((data[2] << 8) | data[3]) 
        az = ((data[4] << 8) | data[5])
        
        if ax > 32767: ax -= 65536
        if ay > 32767: ay -= 65536
        if az > 32767: az -= 65536
        
        # Scale to g's (assuming ±2g range)
        ax_g = ax / 16384.0
        ay_g = ay / 16384.0
        az_g = az / 16384.0
        
        print(f"✅ Raw accelerometer data:")
        print(f"   X: {ax_g:.3f}g")
        print(f"   Y: {ay_g:.3f}g") 
        print(f"   Z: {az_g:.3f}g")
        
        # Check if data looks reasonable (gravity should be ~1g total)
        total_g = (ax_g**2 + ay_g**2 + az_g**2)**0.5
        print(f"   Total magnitude: {total_g:.3f}g")
        
        if 0.5 < total_g < 2.0:
            print("✅ Sensor data looks good!")
            return True
        else:
            print("⚠️  Sensor data seems unusual")
            return False
            
    except Exception as e:
        print(f"❌ Sensor test failed: {e}")
        return False

if __name__ == "__main__":
    identify_imu_sensor()

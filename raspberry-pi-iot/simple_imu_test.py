#!/usr/bin/env python3
"""
Simple IMU Test - Just for testing the MPU6050/MPU9250 sensor
"""

import smbus2
import time
import struct

# I2C configuration
I2C_BUS = 1
MPU_ADDR = 0x68

def init_mpu():
    """Initialize the MPU sensor"""
    bus = smbus2.SMBus(I2C_BUS)
    
    # Wake up the sensor
    bus.write_byte_data(MPU_ADDR, 0x6B, 0)
    time.sleep(0.1)
    
    # Configure accelerometer and gyroscope ranges
    bus.write_byte_data(MPU_ADDR, 0x1C, 0x00)  # ±2g
    bus.write_byte_data(MPU_ADDR, 0x1B, 0x00)  # ±250°/s
    
    return bus

def read_raw_data(bus, addr):
    """Read raw 16-bit data from sensor"""
    high = bus.read_byte_data(MPU_ADDR, addr)
    low = bus.read_byte_data(MPU_ADDR, addr + 1)
    
    # Combine high and low bytes
    value = (high << 8) | low
    
    # Convert to signed 16-bit
    if value > 32768:
        value = value - 65536
    
    return value

def read_imu_data(bus):
    """Read accelerometer, gyroscope, and temperature data"""
    
    # Read accelerometer data (registers 0x3B to 0x40)
    acc_x = read_raw_data(bus, 0x3B) / 16384.0  # Convert to g
    acc_y = read_raw_data(bus, 0x3D) / 16384.0
    acc_z = read_raw_data(bus, 0x3F) / 16384.0
    
    # Read temperature (registers 0x41 to 0x42)
    temp_raw = read_raw_data(bus, 0x41)
    temp_c = (temp_raw / 340.0) + 36.53
    
    # Read gyroscope data (registers 0x43 to 0x48)
    gyro_x = read_raw_data(bus, 0x43) / 131.0  # Convert to °/s
    gyro_y = read_raw_data(bus, 0x45) / 131.0
    gyro_z = read_raw_data(bus, 0x47) / 131.0
    
    return {
        'acc_x': acc_x, 'acc_y': acc_y, 'acc_z': acc_z,
        'gyro_x': gyro_x, 'gyro_y': gyro_y, 'gyro_z': gyro_z,
        'temp': temp_c
    }

def main():
    print("🚀 Simple IMU Test")
    print("=" * 40)
    
    try:
        # Check WHO_AM_I register
        bus = smbus2.SMBus(I2C_BUS)
        who_am_i = bus.read_byte_data(MPU_ADDR, 0x75)
        
        sensor_types = {
            0x68: "MPU6050",
            0x70: "MPU6500", 
            0x71: "MPU9250",
            0x73: "MPU9255"
        }
        
        sensor_name = sensor_types.get(who_am_i, f"Unknown (0x{who_am_i:02X})")
        print(f"✅ Detected: {sensor_name} at 0x{MPU_ADDR:02X}")
        
        # Initialize sensor
        print("🔧 Initializing sensor...")
        bus = init_mpu()
        time.sleep(0.5)
        
        print("📊 Reading IMU data for 10 seconds...")
        print("   (Move the device to see changes)")
        print()
        print("Time   | Accel (g)        | Gyro (°/s)       | Temp(°C)")
        print("-------|------------------|------------------|----------")
        
        start_time = time.time()
        while time.time() - start_time < 10:
            data = read_imu_data(bus)
            
            elapsed = time.time() - start_time
            print(f"{elapsed:6.1f} | "
                  f"{data['acc_x']:6.2f},{data['acc_y']:6.2f},{data['acc_z']:6.2f} | "
                  f"{data['gyro_x']:6.1f},{data['gyro_y']:6.1f},{data['gyro_z']:6.1f} | "
                  f"{data['temp']:6.1f}")
            
            time.sleep(0.2)
        
        print("\n✅ IMU test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure:")
        print("   - I2C is enabled (sudo raspi-config)")
        print("   - IMU sensor is properly wired")
        print("   - VCC → 3.3V, GND → GND, SDA → GPIO2, SCL → GPIO3")

if __name__ == "__main__":
    main()

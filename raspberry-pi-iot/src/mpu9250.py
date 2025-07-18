"""
MPU-9250 IMU Sensor Module
Handles communication with the MPU-9250 9-axis IMU sensor via I2C
"""

import smbus2
import time
import struct
import logging
from typing import Dict, Tuple, Optional
from config import I2CConfig

logger = logging.getLogger(__name__)

class MPU9250:
    """MPU-9250 9-axis IMU sensor driver"""
    
    # Register addresses
    WHO_AM_I = 0x75
    PWR_MGMT_1 = 0x6B
    PWR_MGMT_2 = 0x6C
    CONFIG = 0x1A
    GYRO_CONFIG = 0x1B
    ACCEL_CONFIG = 0x1C
    ACCEL_CONFIG2 = 0x1D
    
    # Data registers
    ACCEL_XOUT_H = 0x3B
    GYRO_XOUT_H = 0x43
    TEMP_OUT_H = 0x41
    
    # Magnetometer (AK8963) registers
    MAG_ADDRESS = 0x0C
    MAG_CNTL1 = 0x0A
    MAG_XOUT_L = 0x03
    
    def __init__(self, bus_number: int = I2CConfig.BUS_NUMBER, 
                 address: int = I2CConfig.MPU9250_ADDRESS):
        """Initialize MPU-9250 sensor"""
        self.bus_number = bus_number
        self.address = address
        self.bus = None
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the MPU-9250 sensor"""
        try:
            self.bus = smbus2.SMBus(self.bus_number)
            
            # Check device ID
            device_id = self.bus.read_byte_data(self.address, self.WHO_AM_I)
            if device_id not in [0x71, 0x73]:  # Valid MPU-9250 IDs
                logger.error(f"Invalid device ID: 0x{device_id:02X}")
                return False
            
            # Reset device
            self.bus.write_byte_data(self.address, self.PWR_MGMT_1, 0x80)
            await asyncio.sleep(0.1)
            
            # Wake up device
            self.bus.write_byte_data(self.address, self.PWR_MGMT_1, 0x00)
            await asyncio.sleep(0.1)
            
            # Configure gyroscope (±2000 dps)
            self.bus.write_byte_data(self.address, self.GYRO_CONFIG, 0x18)
            
            # Configure accelerometer (±16g)
            self.bus.write_byte_data(self.address, self.ACCEL_CONFIG, 0x18)
            
            # Set sample rate (1kHz / (1 + 19) = 50Hz)
            self.bus.write_byte_data(self.address, 0x19, 19)
            
            # Configure low-pass filter
            self.bus.write_byte_data(self.address, self.CONFIG, 0x03)
            
            self.is_initialized = True
            logger.info("MPU-9250 initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MPU-9250: {e}")
            return False
    
    def read_accelerometer(self) -> Tuple[float, float, float]:
        """Read accelerometer data in g units"""
        if not self.is_initialized:
            raise RuntimeError("MPU-9250 not initialized")
        
        try:
            # Read 6 bytes starting from ACCEL_XOUT_H
            data = self.bus.read_i2c_block_data(self.address, self.ACCEL_XOUT_H, 6)
            
            # Convert to signed 16-bit values
            ax = struct.unpack('>h', bytes(data[0:2]))[0]
            ay = struct.unpack('>h', bytes(data[2:4]))[0]
            az = struct.unpack('>h', bytes(data[4:6]))[0]
            
            # Convert to g units (±16g range)
            ax_g = ax / 2048.0
            ay_g = ay / 2048.0
            az_g = az / 2048.0
            
            return ax_g, ay_g, az_g
            
        except Exception as e:
            logger.error(f"Failed to read accelerometer: {e}")
            return 0.0, 0.0, 0.0
    
    def read_gyroscope(self) -> Tuple[float, float, float]:
        """Read gyroscope data in degrees/second"""
        if not self.is_initialized:
            raise RuntimeError("MPU-9250 not initialized")
        
        try:
            # Read 6 bytes starting from GYRO_XOUT_H
            data = self.bus.read_i2c_block_data(self.address, self.GYRO_XOUT_H, 6)
            
            # Convert to signed 16-bit values
            gx = struct.unpack('>h', bytes(data[0:2]))[0]
            gy = struct.unpack('>h', bytes(data[2:4]))[0]
            gz = struct.unpack('>h', bytes(data[4:6]))[0]
            
            # Convert to degrees/second (±2000 dps range)
            gx_dps = gx / 16.384
            gy_dps = gy / 16.384
            gz_dps = gz / 16.384
            
            return gx_dps, gy_dps, gz_dps
            
        except Exception as e:
            logger.error(f"Failed to read gyroscope: {e}")
            return 0.0, 0.0, 0.0
    
    def read_temperature(self) -> float:
        """Read temperature in Celsius"""
        if not self.is_initialized:
            raise RuntimeError("MPU-9250 not initialized")
        
        try:
            # Read 2 bytes starting from TEMP_OUT_H
            data = self.bus.read_i2c_block_data(self.address, self.TEMP_OUT_H, 2)
            temp_raw = struct.unpack('>h', bytes(data))[0]
            
            # Convert to Celsius
            temp_c = (temp_raw / 333.87) + 21.0
            
            return temp_c
            
        except Exception as e:
            logger.error(f"Failed to read temperature: {e}")
            return 0.0
    
    async def read_all_sensors(self) -> Dict[str, Dict[str, float]]:
        """Read all sensor data"""
        try:
            accel_x, accel_y, accel_z = self.read_accelerometer()
            gyro_x, gyro_y, gyro_z = self.read_gyroscope()
            temperature = self.read_temperature()
            
            return {
                "accelerometer": {
                    "x": accel_x,
                    "y": accel_y,
                    "z": accel_z,
                    "unit": "g"
                },
                "gyroscope": {
                    "x": gyro_x,
                    "y": gyro_y,
                    "z": gyro_z,
                    "unit": "dps"
                },
                "temperature": {
                    "value": temperature,
                    "unit": "celsius"
                },
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to read all sensors: {e}")
            return {}
    
    def close(self):
        """Close I2C bus connection"""
        if self.bus:
            self.bus.close()
            self.is_initialized = False
            logger.info("MPU-9250 connection closed")

import asyncio

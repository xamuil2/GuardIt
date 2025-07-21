import smbus2
import time

def identify_imu_sensor():

    bus = smbus2.SMBus(1)
    
    try:
        who_am_i = bus.read_byte_data(0x68, 0x75)
        
        sensor_map = {
            0x68: "MPU6050",
            0x70: "MPU6500", 
            0x71: "MPU9250",
            0x73: "MPU9255"
        }
        
        sensor_name = sensor_map.get(who_am_i, f"Unknown (0x{who_am_i:02X})")
        
        if who_am_i in [0x68, 0x70, 0x71, 0x73]:
            test_sensor_basic(bus)
        else:
            
    except Exception as e:
    finally:
        bus.close()

def test_sensor_basic(bus):

    try:
        bus.write_byte_data(0x68, 0x6B, 0)
        time.sleep(0.1)
        
        data = bus.read_i2c_block_data(0x68, 0x3B, 6)
        
        ax = ((data[0] << 8) | data[1])
        ay = ((data[2] << 8) | data[3]) 
        az = ((data[4] << 8) | data[5])
        
        if ax > 32767: ax -= 65536
        if ay > 32767: ay -= 65536
        if az > 32767: az -= 65536
        
        ax_g = ax / 16384.0
        ay_g = ay / 16384.0
        az_g = az / 16384.0

        total_g = (ax_g**2 + ay_g**2 + az_g**2)**0.5
        
        if 0.5 < total_g < 2.0:
            return True
        else:
            return False
            
    except Exception as e:
        return False

if __name__ == "__main__":
    identify_imu_sensor()

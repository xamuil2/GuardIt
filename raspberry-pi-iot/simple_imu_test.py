import smbus2
import time
import struct

I2C_BUS = 1
MPU_ADDR = 0x68

def init_mpu():
    
    bus = smbus2.SMBus(I2C_BUS)
    
    bus.write_byte_data(MPU_ADDR, 0x6B, 0)
    time.sleep(0.1)
    
    bus.write_byte_data(MPU_ADDR, 0x1C, 0x00)
    bus.write_byte_data(MPU_ADDR, 0x1B, 0x00)
    
    return bus

def read_raw_data(bus, addr):
    
    high = bus.read_byte_data(MPU_ADDR, addr)
    low = bus.read_byte_data(MPU_ADDR, addr + 1)
    
    value = (high << 8) | low
    
    if value > 32768:
        value = value - 65536
    
    return value

def read_imu_data(bus):

    acc_x = read_raw_data(bus, 0x3B) / 16384.0
    acc_y = read_raw_data(bus, 0x3D) / 16384.0
    acc_z = read_raw_data(bus, 0x3F) / 16384.0
    
    temp_raw = read_raw_data(bus, 0x41)
    temp_c = (temp_raw / 340.0) + 36.53
    
    gyro_x = read_raw_data(bus, 0x43) / 131.0
    gyro_y = read_raw_data(bus, 0x45) / 131.0
    gyro_z = read_raw_data(bus, 0x47) / 131.0
    
    return {
        'acc_x': acc_x, 'acc_y': acc_y, 'acc_z': acc_z,
        'gyro_x': gyro_x, 'gyro_y': gyro_y, 'gyro_z': gyro_z,
        'temp': temp_c
    }

def main():
    
    try:
        bus = smbus2.SMBus(I2C_BUS)
        who_am_i = bus.read_byte_data(MPU_ADDR, 0x75)
        
        sensor_types = {
            0x68: "MPU6050",
            0x70: "MPU6500", 
            0x71: "MPU9250",
            0x73: "MPU9255"
        }
        
        sensor_name = sensor_types.get(who_am_i, f"Unknown (0x{who_am_i:02X})")
        
        bus = init_mpu()
        time.sleep(0.5)

        start_time = time.time()
        while time.time() - start_time < 10:
            data = read_imu_data(bus)
            
            elapsed = time.time() - start_time
                  f"{data['acc_x']:6.2f},{data['acc_y']:6.2f},{data['acc_z']:6.2f} | "
                  f"{data['gyro_x']:6.1f},{data['gyro_y']:6.1f},{data['gyro_z']:6.1f} | "
                  f"{data['temp']:6.1f}")
            
            time.sleep(0.2)

    except Exception as e:

if __name__ == "__main__":
    main()

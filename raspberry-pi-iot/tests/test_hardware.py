#!/usr/bin/env python3
"""
Hardware Test Script
Test individual hardware components
"""

import asyncio
import sys
import time
sys.path.append('..')

from src.mpu9250 import MPU9250
from src.hardware_controller import HardwareController, Colors, Notes
from src.camera_manager import CameraManager

async def test_imu():
    """Test MPU-9250 IMU sensor"""
    print("Testing MPU-9250 IMU sensor...")
    
    imu = MPU9250()
    if await imu.initialize():
        print("✓ IMU initialized successfully")
        
        # Read sensor data
        for i in range(5):
            data = await imu.read_all_sensors()
            if data:
                print(f"Reading {i+1}:")
                print(f"  Accelerometer: {data['accelerometer']}")
                print(f"  Gyroscope: {data['gyroscope']}")
                print(f"  Temperature: {data['temperature']}")
                print()
            await asyncio.sleep(0.1)
        
        imu.close()
        print("✓ IMU test completed")
    else:
        print("✗ Failed to initialize IMU")

async def test_hardware():
    """Test RGB LED and buzzer"""
    print("Testing hardware controller...")
    
    hw = HardwareController()
    if await hw.initialize():
        print("✓ Hardware controller initialized successfully")
        
        # Test RGB LED
        print("Testing RGB LED...")
        colors = [Colors.RED, Colors.GREEN, Colors.BLUE, Colors.WHITE, Colors.OFF]
        color_names = ["Red", "Green", "Blue", "White", "Off"]
        
        for color, name in zip(colors, color_names):
            print(f"  Setting LED to {name}")
            await hw.set_led_color(*color)
            await asyncio.sleep(1)
        
        # Test buzzer
        print("Testing buzzer...")
        notes = [Notes.C4, Notes.E4, Notes.G4, Notes.C5]
        for note in notes:
            print(f"  Playing note at {note}Hz")
            await hw.play_buzzer_tone(note, 0.5)
            await asyncio.sleep(0.1)
        
        hw.cleanup()
        print("✓ Hardware test completed")
    else:
        print("✗ Failed to initialize hardware controller")

async def test_cameras():
    """Test camera functionality"""
    print("Testing camera manager...")
    
    cam = CameraManager()
    if await cam.initialize():
        print("✓ Camera manager initialized successfully")
        
        # Get camera info
        info = cam.get_all_camera_info()
        print("Camera information:")
        for cam_type, cam_info in info.items():
            print(f"  {cam_type.upper()}: {cam_info}")
        
        # Test streaming for a few seconds
        print("Testing camera streaming for 5 seconds...")
        cam.start_streaming('csi')
        cam.start_streaming('usb')
        
        for i in range(50):  # 5 seconds at 10fps
            csi_frame = cam.get_frame('csi')
            usb_frame = cam.get_frame('usb')
            
            print(f"\rFrame {i+1}/50 - CSI: {'✓' if csi_frame else '✗'}, "
                  f"USB: {'✓' if usb_frame else '✗'}", end='')
            
            await asyncio.sleep(0.1)
        
        print("\n✓ Camera test completed")
        cam.cleanup()
    else:
        print("✗ Failed to initialize camera manager")

async def main():
    """Run all hardware tests"""
    print("=== Raspberry Pi IoT Hardware Test ===\n")
    
    try:
        await test_imu()
        print()
        await test_hardware()
        print()
        await test_cameras()
        print()
        print("=== All tests completed ===")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import sys
import time
sys.path.append('..')

from src.mpu9250 import MPU9250
from src.hardware_controller import HardwareController, Colors, Notes
from src.camera_manager import CameraManager

async def test_imu():

    imu = MPU9250()
    if await imu.initialize():
        
        for i in range(5):
            data = await imu.read_all_sensors()
            if data:
            await asyncio.sleep(0.1)
        
        imu.close()
    else:

async def test_hardware():

    hw = HardwareController()
    if await hw.initialize():
        
        colors = [Colors.RED, Colors.GREEN, Colors.BLUE, Colors.WHITE, Colors.OFF]
        color_names = ["Red", "Green", "Blue", "White", "Off"]
        
        for color, name in zip(colors, color_names):
            await hw.set_led_color(*color)
            await asyncio.sleep(1)
        
        notes = [Notes.C4, Notes.E4, Notes.G4, Notes.C5]
        for note in notes:
            await hw.play_buzzer_tone(note, 0.5)
            await asyncio.sleep(0.1)
        
        hw.cleanup()
    else:

async def test_cameras():

    cam = CameraManager()
    if await cam.initialize():
        
        info = cam.get_all_camera_info()
        for cam_type, cam_info in info.items():
        
        cam.start_streaming('csi')
        cam.start_streaming('usb')
        
        for i in range(50):
            csi_frame = cam.get_frame('csi')
            usb_frame = cam.get_frame('usb')
            
                  f"USB: {'✓' if usb_frame else '✗'}", end='')
            
            await asyncio.sleep(0.1)
        
        cam.cleanup()
    else:

async def main():

    try:
        await test_imu()
        await test_hardware()
        await test_cameras()
    except KeyboardInterrupt:
    except Exception as e:

if __name__ == "__main__":
    asyncio.run(main())

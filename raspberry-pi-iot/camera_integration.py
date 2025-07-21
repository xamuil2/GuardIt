import cv2
import numpy as np
import time
import subprocess
import threading
import base64
import io
from PIL import Image
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GuardItCameraManager:
    def __init__(self):
        self.csi_available = False
        self.usb_available = False
        self.usb_device_id = None
        self.streaming = False
        self.frame_callbacks = []
        
        self._detect_cameras()
    
    def _detect_cameras(self):
        
        logger.info("🔍 Detecting cameras...")
        
        try:
            result = subprocess.run(
                ["libcamera-hello", "--list-cameras"], 
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and "imx219" in result.stdout:
                self.csi_available = True
                logger.info("✅ CSI Camera (imx219) detected")
            else:
                logger.warning("❌ CSI Camera not detected")
        except Exception as e:
            logger.warning(f"❌ CSI Camera detection failed: {e}")
        
        for device_id in [1, 0, 2]:
            cap = cv2.VideoCapture(device_id, cv2.CAP_V4L2)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    self.usb_available = True
                    self.usb_device_id = device_id
                    logger.info(f"✅ USB Camera detected on device {device_id}")
                    cap.release()
                    break
            cap.release()
        
        if not self.usb_available:
            logger.warning("❌ No USB Camera detected")
    
    def capture_csi_image(self, width=640, height=480, output_path=None):
        
        if not self.csi_available:
            raise ValueError("CSI camera not available")
        
        if output_path is None:
            output_path = f"/tmp/csi_capture_{int(time.time())}.jpg"
        
        try:
            result = subprocess.run([
                "libcamera-still",
                "-o", output_path,
                "-t", "1000",
                "--width", str(width),
                "--height", str(height),
                "-n"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info(f"📸 CSI image captured: {output_path}")
                return output_path
            else:
                raise RuntimeError(f"libcamera-still failed: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("CSI camera capture timed out")
    
    def capture_usb_image(self, width=640, height=480, output_path=None):
        
        if not self.usb_available:
            raise ValueError("USB camera not available")
        
        if output_path is None:
            output_path = f"/tmp/usb_capture_{int(time.time())}.jpg"
        
        cap = cv2.VideoCapture(self.usb_device_id, cv2.CAP_V4L2)
        try:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            ret, frame = cap.read()
            if ret and frame is not None:
                cv2.imwrite(output_path, frame)
                logger.info(f"📸 USB image captured: {output_path}")
                return output_path
            else:
                raise RuntimeError("Failed to capture USB camera frame")
        
        finally:
            cap.release()
    
    def get_usb_video_stream(self, width=320, height=240):
        
        if not self.usb_available:
            raise ValueError("USB camera not available")
        
        cap = cv2.VideoCapture(self.usb_device_id, cv2.CAP_V4L2)
        try:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, 15)
            
            while self.streaming:
                ret, frame = cap.read()
                if ret and frame is not None:
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    frame_bytes = buffer.tobytes()
                    
                    frame_b64 = base64.b64encode(frame_bytes).decode('utf-8')
                    
                    yield {
                        'timestamp': time.time(),
                        'camera': 'usb',
                        'format': 'jpeg',
                        'data': frame_b64,
                        'size': len(frame_bytes)
                    }
                
                time.sleep(0.066)
        
        finally:
            cap.release()
    
    def start_streaming(self):
        
        self.streaming = True
        logger.info("🎬 Camera streaming started")
    
    def stop_streaming(self):
        
        self.streaming = False
        logger.info("⏹️  Camera streaming stopped")
    
    async def get_dual_capture(self):
        
        if not (self.csi_available and self.usb_available):
            raise ValueError("Both cameras required for dual capture")
        
        logger.info("📷 Starting dual camera capture...")
        
        async def csi_task():
            return await asyncio.get_event_loop().run_in_executor(
                None, self.capture_csi_image
            )
        
        async def usb_task():
            return await asyncio.get_event_loop().run_in_executor(
                None, self.capture_usb_image
            )
        
        csi_path, usb_path = await asyncio.gather(csi_task(), usb_task())
        
        return {
            'csi_image': csi_path,
            'usb_image': usb_path,
            'timestamp': time.time()
        }
    
    def get_camera_status(self):
        
        return {
            'csi_available': self.csi_available,
            'usb_available': self.usb_available,
            'usb_device_id': self.usb_device_id,
            'streaming': self.streaming,
            'capabilities': {
                'single_capture': self.csi_available or self.usb_available,
                'dual_capture': self.csi_available and self.usb_available,
                'video_streaming': self.usb_available
            }
        }

def demo_camera_integration():

    cam_manager = GuardItCameraManager()
    
    status = cam_manager.get_camera_status()
    
    if status['csi_available']:
        try:
            csi_path = cam_manager.capture_csi_image()
        except Exception as e:
    
    if status['usb_available']:
        try:
            usb_path = cam_manager.capture_usb_image()
        except Exception as e:
    
    if status['capabilities']['dual_capture']:
        async def test_dual():
            try:
                result = await cam_manager.get_dual_capture()
                return True
            except Exception as e:
                return False
        
        import asyncio
        asyncio.run(test_dual())
    
    if status['capabilities']['video_streaming']:
        cam_manager.start_streaming()
        
        frame_count = 0
        start_time = time.time()
        
        for frame_data in cam_manager.get_usb_video_stream():
            frame_count += 1
            if frame_count % 10 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
            
            if time.time() - start_time > 5:
                break
        
        cam_manager.stop_streaming()

if __name__ == "__main__":
    demo_camera_integration()

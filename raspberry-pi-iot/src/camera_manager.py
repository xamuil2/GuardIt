"""
Camera Manager Module
Handles dual camera streaming (CSI and USB webcam)
"""

import cv2
import asyncio
import logging
import threading
from typing import Optional, Iterator
import time
from config import CameraConfig

logger = logging.getLogger(__name__)

class CameraManager:
    """Manages dual camera streaming for IoT device"""
    
    def __init__(self):
        """Initialize camera manager"""
        self.csi_camera = None
        self.usb_camera = None
        self.is_streaming = {'csi': False, 'usb': False}
        self.frame_cache = {'csi': None, 'usb': None}
        self.capture_threads = {'csi': None, 'usb': None}
        self.stop_events = {'csi': threading.Event(), 'usb': threading.Event()}
        
    async def initialize(self) -> bool:
        """Initialize both cameras"""
        success = True
        
        # Initialize CSI camera
        try:
            self.csi_camera = cv2.VideoCapture(CameraConfig.CSI_CAMERA_INDEX)
            if self.csi_camera.isOpened():
                self.csi_camera.set(cv2.CAP_PROP_FRAME_WIDTH, CameraConfig.FRAME_WIDTH)
                self.csi_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CameraConfig.FRAME_HEIGHT)
                self.csi_camera.set(cv2.CAP_PROP_FPS, CameraConfig.FPS)
                logger.info("CSI camera initialized successfully")
            else:
                logger.warning("Failed to initialize CSI camera")
                self.csi_camera = None
                success = False
        except Exception as e:
            logger.error(f"Error initializing CSI camera: {e}")
            self.csi_camera = None
            success = False
        
        # Initialize USB camera
        try:
            self.usb_camera = cv2.VideoCapture(CameraConfig.USB_CAMERA_INDEX)
            if self.usb_camera.isOpened():
                self.usb_camera.set(cv2.CAP_PROP_FRAME_WIDTH, CameraConfig.FRAME_WIDTH)
                self.usb_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CameraConfig.FRAME_HEIGHT)
                self.usb_camera.set(cv2.CAP_PROP_FPS, CameraConfig.FPS)
                logger.info("USB camera initialized successfully")
            else:
                logger.warning("Failed to initialize USB camera")
                self.usb_camera = None
        except Exception as e:
            logger.error(f"Error initializing USB camera: {e}")
            self.usb_camera = None
        
        return success or self.usb_camera is not None
    
    def _capture_frames(self, camera_type: str):
        """Capture frames in a separate thread"""
        camera = self.csi_camera if camera_type == 'csi' else self.usb_camera
        if not camera:
            return
        
        logger.info(f"Starting {camera_type} camera capture thread")
        
        while not self.stop_events[camera_type].is_set():
            try:
                ret, frame = camera.read()
                if ret:
                    self.frame_cache[camera_type] = frame
                else:
                    logger.warning(f"Failed to read frame from {camera_type} camera")
                    break
                    
                # Control frame rate
                time.sleep(1.0 / CameraConfig.FPS)
                
            except Exception as e:
                logger.error(f"Error capturing {camera_type} frame: {e}")
                break
        
        logger.info(f"{camera_type} camera capture thread stopped")
    
    def start_streaming(self, camera_type: str) -> bool:
        """Start streaming for specified camera"""
        if camera_type not in ['csi', 'usb']:
            raise ValueError("camera_type must be 'csi' or 'usb'")
        
        camera = self.csi_camera if camera_type == 'csi' else self.usb_camera
        if not camera or not camera.isOpened():
            logger.error(f"{camera_type} camera not available")
            return False
        
        if self.is_streaming[camera_type]:
            logger.warning(f"{camera_type} camera already streaming")
            return True
        
        # Reset stop event
        self.stop_events[camera_type].clear()
        
        # Start capture thread
        self.capture_threads[camera_type] = threading.Thread(
            target=self._capture_frames, 
            args=(camera_type,),
            daemon=True
        )
        self.capture_threads[camera_type].start()
        
        self.is_streaming[camera_type] = True
        logger.info(f"Started streaming {camera_type} camera")
        return True
    
    def stop_streaming(self, camera_type: str):
        """Stop streaming for specified camera"""
        if camera_type not in ['csi', 'usb']:
            raise ValueError("camera_type must be 'csi' or 'usb'")
        
        if not self.is_streaming[camera_type]:
            return
        
        # Signal thread to stop
        self.stop_events[camera_type].set()
        
        # Wait for thread to finish
        if self.capture_threads[camera_type]:
            self.capture_threads[camera_type].join(timeout=2.0)
        
        self.is_streaming[camera_type] = False
        self.frame_cache[camera_type] = None
        logger.info(f"Stopped streaming {camera_type} camera")
    
    def get_frame(self, camera_type: str) -> Optional[bytes]:
        """Get current frame as JPEG bytes"""
        if camera_type not in ['csi', 'usb']:
            raise ValueError("camera_type must be 'csi' or 'usb'")
        
        if not self.is_streaming[camera_type]:
            return None
        
        frame = self.frame_cache[camera_type]
        if frame is None:
            return None
        
        try:
            # Encode frame as JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, CameraConfig.QUALITY]
            ret, buffer = cv2.imencode('.jpg', frame, encode_params)
            
            if ret:
                return buffer.tobytes()
            else:
                logger.error(f"Failed to encode {camera_type} frame")
                return None
                
        except Exception as e:
            logger.error(f"Error encoding {camera_type} frame: {e}")
            return None
    
    def generate_mjpeg_stream(self, camera_type: str) -> Iterator[bytes]:
        """Generate MJPEG stream for HTTP streaming"""
        if camera_type not in ['csi', 'usb']:
            raise ValueError("camera_type must be 'csi' or 'usb'")
        
        while self.is_streaming[camera_type]:
            frame_bytes = self.get_frame(camera_type)
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # If no frame available, wait a bit
                time.sleep(0.1)
    
    def get_camera_info(self, camera_type: str) -> dict:
        """Get camera information"""
        if camera_type not in ['csi', 'usb']:
            raise ValueError("camera_type must be 'csi' or 'usb'")
        
        camera = self.csi_camera if camera_type == 'csi' else self.usb_camera
        
        if not camera or not camera.isOpened():
            return {
                "type": camera_type,
                "available": False,
                "streaming": False
            }
        
        return {
            "type": camera_type,
            "available": True,
            "streaming": self.is_streaming[camera_type],
            "width": int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": int(camera.get(cv2.CAP_PROP_FPS))
        }
    
    def get_all_camera_info(self) -> dict:
        """Get information about all cameras"""
        return {
            "csi": self.get_camera_info("csi"),
            "usb": self.get_camera_info("usb")
        }
    
    def cleanup(self):
        """Clean up camera resources"""
        logger.info("Cleaning up camera resources")
        
        # Stop streaming for both cameras
        self.stop_streaming('csi')
        self.stop_streaming('usb')
        
        # Release camera resources
        if self.csi_camera:
            self.csi_camera.release()
            self.csi_camera = None
        
        if self.usb_camera:
            self.usb_camera.release()
            self.usb_camera = None
        
        logger.info("Camera cleanup completed")

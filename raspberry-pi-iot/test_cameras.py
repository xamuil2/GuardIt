import cv2
import numpy as np
import time
from picamera2 import Picamera2
import threading
import sys

class CameraTestManager:
    def __init__(self):
        self.csi_camera = None
        self.usb_camera = None
        self.running = False

    def test_csi_camera(self):
        
        try:
            self.csi_camera = Picamera2()
            
            config = self.csi_camera.create_preview_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            self.csi_camera.configure(config)
            
            self.csi_camera.start()
            
            time.sleep(2)
            frame = self.csi_camera.capture_array()
            
            if frame is not None:
                
                cv2.imwrite("/home/guardit/Documents/GuardIt/raspberry-pi-iot/csi_test.jpg", 
                           cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                return True
            else:
                return False
                
        except Exception as e:
            return False
        finally:
            if self.csi_camera:
                self.csi_camera.stop()
                self.csi_camera.close()

    def test_usb_camera(self, device_id=1):
        
        try:
            self.usb_camera = cv2.VideoCapture(device_id)
            
            if not self.usb_camera.isOpened():
                return False
            
            self.usb_camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.usb_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.usb_camera.set(cv2.CAP_PROP_FPS, 30)

            time.sleep(1)
            ret, frame = self.usb_camera.read()
            
            if ret and frame is not None:
                
                cv2.imwrite("/home/guardit/Documents/GuardIt/raspberry-pi-iot/usb_test.jpg", frame)
                return True
            else:
                return False
                
        except Exception as e:
            return False
        finally:
            if self.usb_camera:
                self.usb_camera.release()

    def test_dual_camera_streaming(self, duration=10):

        try:
            self.csi_camera = Picamera2()
            config = self.csi_camera.create_preview_configuration(
                main={"size": (320, 240), "format": "RGB888"}
            )
            self.csi_camera.configure(config)
            self.csi_camera.start()
            
            self.usb_camera = cv2.VideoCapture(1)
            self.usb_camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.usb_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            
            if not self.usb_camera.isOpened():
                return False

            start_time = time.time()
            frame_count = 0
            
            while time.time() - start_time < duration:
                try:
                    csi_frame = self.csi_camera.capture_array()
                    
                    ret, usb_frame = self.usb_camera.read()
                    
                    if csi_frame is not None and ret:
                        frame_count += 1
                        if frame_count % 30 == 0:
                    
                    time.sleep(0.033)
                    
                except Exception as e:
                    continue
            
            elapsed = time.time() - start_time
            fps = frame_count / elapsed
            
            return True
            
        except Exception as e:
            return False
        finally:
            if self.csi_camera:
                self.csi_camera.stop()
                self.csi_camera.close()
            if self.usb_camera:
                self.usb_camera.release()

    def run_all_tests(self):

        csi_result = self.test_csi_camera()
        
        usb_result = False
        for device_id in [1, 0, 2]:
            usb_result = self.test_usb_camera(device_id)
            if usb_result:
                break
        
        if csi_result and usb_result:
            dual_result = self.test_dual_camera_streaming(duration=5)
        else:
            dual_result = False

        if csi_result and usb_result:
        else:
        
        return csi_result, usb_result, dual_result

if __name__ == "__main__":
    tester = CameraTestManager()
    tester.run_all_tests()

import cv2
import numpy as np
import time
import subprocess
import os

class SimpleCameraTest:
    def __init__(self):
        self.test_results = {}

    def check_video_devices(self):
        
        try:
            devices = []
            for i in range(10):
                device_path = f"/dev/video{i}"
                if os.path.exists(device_path):
                    devices.append(i)
            
            return devices
        except Exception as e:
            return []

    def test_libcamera_csi(self):
        
        try:
            output_file = "/home/guardit/Documents/GuardIt/raspberry-pi-iot/csi_test_libcamera.jpg"
            
            result = subprocess.run([
                "libcamera-still", 
                "-o", output_file,
                "-t", "1000",
                "--width", "640",
                "--height", "480"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                return True
            else:
                return False
                
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            return False

    def test_opencv_camera(self, device_id=0, camera_name="Camera"):
        
        cap = None
        try:
            backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
            
            for backend in backends:
                cap = cv2.VideoCapture(device_id, backend)
                
                if cap.isOpened():
                    break
                else:
                    if cap:
                        cap.release()
                    cap = None
            
            if not cap or not cap.isOpened():
                return False
            
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            for attempt in range(5):
                ret, frame = cap.read()
                if ret and frame is not None:
                    
                    output_file = f"/home/guardit/Documents/GuardIt/raspberry-pi-iot/{camera_name.lower()}_test_opencv_{device_id}.jpg"
                    cv2.imwrite(output_file, frame)
                    
                    return True
                else:
                    time.sleep(0.5)
            
            return False
            
        except Exception as e:
            return False
        finally:
            if cap:
                cap.release()

    def test_dual_streaming(self, csi_device=0, usb_device=1, duration=5):

        csi_cap = None
        usb_cap = None
        
        try:
            csi_cap = cv2.VideoCapture(csi_device, cv2.CAP_V4L2)
            usb_cap = cv2.VideoCapture(usb_device, cv2.CAP_V4L2)
            
            if not csi_cap.isOpened():
                return False
            
            if not usb_cap.isOpened():
                return False
            
            for cap in [csi_cap, usb_cap]:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                cap.set(cv2.CAP_PROP_FPS, 15)

            start_time = time.time()
            frame_count = 0
            successful_captures = 0
            
            while time.time() - start_time < duration:
                csi_ret, csi_frame = csi_cap.read()
                usb_ret, usb_frame = usb_cap.read()
                
                frame_count += 1
                
                if csi_ret and usb_ret:
                    successful_captures += 1
                    
                    if frame_count % 30 == 0:
                
                time.sleep(0.066)
            
            elapsed = time.time() - start_time
            success_rate = (successful_captures / frame_count) * 100
            avg_fps = frame_count / elapsed

            return success_rate > 50
            
        except Exception as e:
            return False
        finally:
            if csi_cap:
                csi_cap.release()
            if usb_cap:
                usb_cap.release()

    def run_comprehensive_test(self):

        devices = self.check_video_devices()
        
        csi_libcamera_result = self.test_libcamera_csi()
        self.test_results['csi_libcamera'] = csi_libcamera_result
        
        opencv_results = {}
        for device_id in devices[:4]:
            result = self.test_opencv_camera(device_id, f"Device{device_id}")
            opencv_results[device_id] = result
            self.test_results[f'opencv_device_{device_id}'] = result
        
        working_devices = [dev for dev, result in opencv_results.items() if result]
        if len(working_devices) >= 2:
            dual_result = self.test_dual_streaming(
                working_devices[0], 
                working_devices[1], 
                duration=3
            )
            self.test_results['dual_streaming'] = dual_result
        else:
            dual_result = False
            self.test_results['dual_streaming'] = False

        for device_id, result in opencv_results.items():

        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())

        if passed_tests >= total_tests // 2:
        else:
        
        if csi_libcamera_result:
        
        working_opencv = [dev for dev, result in opencv_results.items() if result]
        if working_opencv:
        
        if self.test_results.get('dual_streaming', False):
        
        return self.test_results

if __name__ == "__main__":
    tester = SimpleCameraTest()
    results = tester.run_comprehensive_test()

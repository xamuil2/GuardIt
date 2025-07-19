#!/usr/bin/env python3
"""
Simple Camera Test for GuardIt IoT Project
Tests CSI camera with basic OpenCV and USB camera
"""

import cv2
import numpy as np
import time
import subprocess
import os

class SimpleCameraTest:
    def __init__(self):
        self.test_results = {}

    def check_video_devices(self):
        """Check available video devices"""
        print("🔍 Checking available video devices...")
        try:
            devices = []
            for i in range(10):  # Check first 10 devices
                device_path = f"/dev/video{i}"
                if os.path.exists(device_path):
                    devices.append(i)
            
            print(f"✅ Found video devices: {devices}")
            return devices
        except Exception as e:
            print(f"❌ Error checking devices: {e}")
            return []

    def test_libcamera_csi(self):
        """Test CSI camera using libcamera-still command"""
        print("🎥 Testing CSI Camera (using libcamera-still)...")
        try:
            # Test if libcamera can capture an image
            output_file = "/home/guardit/Documents/GuardIt/raspberry-pi-iot/csi_test_libcamera.jpg"
            
            # Run libcamera-still command
            result = subprocess.run([
                "libcamera-still", 
                "-o", output_file,
                "-t", "1000",  # 1 second timeout
                "--width", "640",
                "--height", "480"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"✅ CSI Camera (libcamera) test successful!")
                print(f"   - Image saved: {output_file}")
                print(f"   - File size: {file_size} bytes")
                return True
            else:
                print(f"❌ CSI Camera (libcamera) failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ CSI Camera (libcamera) timed out")
            return False
        except Exception as e:
            print(f"❌ CSI Camera (libcamera) error: {e}")
            return False

    def test_opencv_camera(self, device_id=0, camera_name="Camera"):
        """Test camera using OpenCV"""
        print(f"📹 Testing {camera_name} (device {device_id}) with OpenCV...")
        cap = None
        try:
            # Try different backends
            backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
            
            for backend in backends:
                print(f"   Trying backend: {backend}")
                cap = cv2.VideoCapture(device_id, backend)
                
                if cap.isOpened():
                    print(f"   ✅ Camera opened with backend {backend}")
                    break
                else:
                    print(f"   ❌ Failed with backend {backend}")
                    if cap:
                        cap.release()
                    cap = None
            
            if not cap or not cap.isOpened():
                print(f"❌ Could not open {camera_name} on device {device_id}")
                return False
            
            # Set properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Get actual properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            print(f"   Camera properties: {width}x{height} @ {fps} FPS")
            
            # Try to capture a frame
            print("   Attempting to capture frame...")
            for attempt in range(5):  # Try multiple times
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"   ✅ Frame captured on attempt {attempt + 1}")
                    print(f"   Frame shape: {frame.shape}")
                    
                    # Save test image
                    output_file = f"/home/guardit/Documents/GuardIt/raspberry-pi-iot/{camera_name.lower()}_test_opencv_{device_id}.jpg"
                    cv2.imwrite(output_file, frame)
                    print(f"   ✅ Test image saved: {output_file}")
                    
                    return True
                else:
                    print(f"   ❌ Frame capture failed on attempt {attempt + 1}")
                    time.sleep(0.5)
            
            print(f"❌ {camera_name} failed to capture any frames")
            return False
            
        except Exception as e:
            print(f"❌ {camera_name} error: {e}")
            return False
        finally:
            if cap:
                cap.release()

    def test_dual_streaming(self, csi_device=0, usb_device=1, duration=5):
        """Test streaming from both cameras simultaneously"""
        print(f"🎬 Testing dual camera streaming for {duration} seconds...")
        
        csi_cap = None
        usb_cap = None
        
        try:
            # Open both cameras
            csi_cap = cv2.VideoCapture(csi_device, cv2.CAP_V4L2)
            usb_cap = cv2.VideoCapture(usb_device, cv2.CAP_V4L2)
            
            if not csi_cap.isOpened():
                print(f"❌ Could not open CSI camera (device {csi_device})")
                return False
            
            if not usb_cap.isOpened():
                print(f"❌ Could not open USB camera (device {usb_device})")
                return False
            
            # Set properties for both cameras
            for cap in [csi_cap, usb_cap]:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                cap.set(cv2.CAP_PROP_FPS, 15)
            
            print("✅ Both cameras opened successfully")
            
            # Stream frames
            start_time = time.time()
            frame_count = 0
            successful_captures = 0
            
            while time.time() - start_time < duration:
                # Capture from both cameras
                csi_ret, csi_frame = csi_cap.read()
                usb_ret, usb_frame = usb_cap.read()
                
                frame_count += 1
                
                if csi_ret and usb_ret:
                    successful_captures += 1
                    
                    if frame_count % 30 == 0:  # Print every 30 frames
                        print(f"   Frame {frame_count}: CSI {csi_frame.shape if csi_ret else 'FAILED'}, USB {usb_frame.shape if usb_ret else 'FAILED'}")
                
                time.sleep(0.066)  # ~15 FPS
            
            elapsed = time.time() - start_time
            success_rate = (successful_captures / frame_count) * 100
            avg_fps = frame_count / elapsed
            
            print(f"✅ Dual streaming completed!")
            print(f"   - Duration: {elapsed:.1f}s")
            print(f"   - Total frames: {frame_count}")
            print(f"   - Successful captures: {successful_captures}")
            print(f"   - Success rate: {success_rate:.1f}%")
            print(f"   - Average FPS: {avg_fps:.1f}")
            
            return success_rate > 50  # Consider successful if >50% frames captured
            
        except Exception as e:
            print(f"❌ Dual streaming error: {e}")
            return False
        finally:
            if csi_cap:
                csi_cap.release()
            if usb_cap:
                usb_cap.release()

    def run_comprehensive_test(self):
        """Run all camera tests"""
        print("🚀 Starting GuardIt Camera Vision Tests")
        print("=" * 60)
        
        # Check available devices
        devices = self.check_video_devices()
        print()
        
        # Test 1: CSI Camera with libcamera
        print("Test 1: CSI Camera (libcamera)")
        print("-" * 30)
        csi_libcamera_result = self.test_libcamera_csi()
        self.test_results['csi_libcamera'] = csi_libcamera_result
        print()
        
        # Test 2: Test cameras with OpenCV on different devices
        opencv_results = {}
        for device_id in devices[:4]:  # Test first 4 devices
            print(f"Test 2.{device_id + 1}: OpenCV Camera on device {device_id}")
            print("-" * 40)
            result = self.test_opencv_camera(device_id, f"Device{device_id}")
            opencv_results[device_id] = result
            self.test_results[f'opencv_device_{device_id}'] = result
            print()
        
        # Test 3: Dual camera streaming (if we have at least 2 working cameras)
        working_devices = [dev for dev, result in opencv_results.items() if result]
        if len(working_devices) >= 2:
            print("Test 3: Dual Camera Streaming")
            print("-" * 30)
            dual_result = self.test_dual_streaming(
                working_devices[0], 
                working_devices[1], 
                duration=3
            )
            self.test_results['dual_streaming'] = dual_result
        else:
            print("Test 3: Dual Camera Streaming")
            print("-" * 30)
            print("⏭️  Skipping dual camera test (need at least 2 working cameras)")
            dual_result = False
            self.test_results['dual_streaming'] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 CAMERA TEST SUMMARY")
        print("=" * 60)
        
        print(f"CSI Camera (libcamera):     {'✅ PASS' if csi_libcamera_result else '❌ FAIL'}")
        
        for device_id, result in opencv_results.items():
            print(f"OpenCV Device {device_id}:          {'✅ PASS' if result else '❌ FAIL'}")
        
        print(f"Dual Camera Streaming:      {'✅ PASS' if self.test_results.get('dual_streaming', False) else '❌ FAIL'}")
        
        # Overall assessment
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests >= total_tests // 2:
            print("🎉 Camera vision system is functional!")
        else:
            print("⚠️  Camera vision system needs attention.")
        
        # Recommendations
        print("\n📋 RECOMMENDATIONS:")
        if csi_libcamera_result:
            print("✅ CSI camera works with libcamera - good for high-quality captures")
        
        working_opencv = [dev for dev, result in opencv_results.items() if result]
        if working_opencv:
            print(f"✅ OpenCV works with devices: {working_opencv} - good for real-time processing")
        
        if self.test_results.get('dual_streaming', False):
            print("✅ Dual camera streaming works - perfect for your IoT monitoring system!")
        
        return self.test_results

if __name__ == "__main__":
    tester = SimpleCameraTest()
    results = tester.run_comprehensive_test()

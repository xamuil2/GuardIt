#!/usr/bin/env python3
"""
Camera Test Script for GuardIt IoT Project
Tests both CSI camera and USB camera functionality
"""

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
        """Test CSI camera using picamera2"""
        print("🎥 Testing CSI Camera (using picamera2)...")
        try:
            # Initialize CSI camera
            self.csi_camera = Picamera2()
            
            # Configure camera
            config = self.csi_camera.create_preview_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            self.csi_camera.configure(config)
            
            # Start camera
            self.csi_camera.start()
            print("✅ CSI Camera initialized successfully!")
            
            # Take a test frame
            time.sleep(2)  # Let camera warm up
            frame = self.csi_camera.capture_array()
            
            if frame is not None:
                print(f"✅ CSI Camera frame captured: {frame.shape}")
                print(f"   - Resolution: {frame.shape[1]}x{frame.shape[0]}")
                print(f"   - Channels: {frame.shape[2] if len(frame.shape) > 2 else 1}")
                
                # Save a test image
                cv2.imwrite("/home/guardit/Documents/GuardIt/raspberry-pi-iot/csi_test.jpg", 
                           cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                print("✅ CSI test image saved as 'csi_test.jpg'")
                return True
            else:
                print("❌ Failed to capture CSI camera frame")
                return False
                
        except Exception as e:
            print(f"❌ CSI Camera error: {e}")
            return False
        finally:
            if self.csi_camera:
                self.csi_camera.stop()
                self.csi_camera.close()

    def test_usb_camera(self, device_id=1):
        """Test USB camera using OpenCV"""
        print(f"📹 Testing USB Camera (device {device_id})...")
        try:
            # Try to open USB camera
            self.usb_camera = cv2.VideoCapture(device_id)
            
            if not self.usb_camera.isOpened():
                print(f"❌ Could not open USB camera on device {device_id}")
                return False
            
            # Set camera properties
            self.usb_camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.usb_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.usb_camera.set(cv2.CAP_PROP_FPS, 30)
            
            print("✅ USB Camera initialized successfully!")
            
            # Capture a test frame
            time.sleep(1)  # Let camera stabilize
            ret, frame = self.usb_camera.read()
            
            if ret and frame is not None:
                print(f"✅ USB Camera frame captured: {frame.shape}")
                print(f"   - Resolution: {frame.shape[1]}x{frame.shape[0]}")
                print(f"   - Channels: {frame.shape[2] if len(frame.shape) > 2 else 1}")
                
                # Save a test image
                cv2.imwrite("/home/guardit/Documents/GuardIt/raspberry-pi-iot/usb_test.jpg", frame)
                print("✅ USB test image saved as 'usb_test.jpg'")
                return True
            else:
                print("❌ Failed to capture USB camera frame")
                return False
                
        except Exception as e:
            print(f"❌ USB Camera error: {e}")
            return False
        finally:
            if self.usb_camera:
                self.usb_camera.release()

    def test_dual_camera_streaming(self, duration=10):
        """Test both cameras streaming simultaneously"""
        print(f"🎬 Testing dual camera streaming for {duration} seconds...")
        
        try:
            # Initialize CSI camera
            self.csi_camera = Picamera2()
            config = self.csi_camera.create_preview_configuration(
                main={"size": (320, 240), "format": "RGB888"}
            )
            self.csi_camera.configure(config)
            self.csi_camera.start()
            
            # Initialize USB camera
            self.usb_camera = cv2.VideoCapture(1)
            self.usb_camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.usb_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            
            if not self.usb_camera.isOpened():
                print("❌ Could not open USB camera for dual streaming")
                return False
            
            print("✅ Both cameras initialized for dual streaming!")
            
            # Stream frames
            start_time = time.time()
            frame_count = 0
            
            while time.time() - start_time < duration:
                try:
                    # Capture from CSI
                    csi_frame = self.csi_camera.capture_array()
                    
                    # Capture from USB
                    ret, usb_frame = self.usb_camera.read()
                    
                    if csi_frame is not None and ret:
                        frame_count += 1
                        if frame_count % 30 == 0:  # Print every 30 frames
                            print(f"   Frame {frame_count}: CSI {csi_frame.shape}, USB {usb_frame.shape}")
                    
                    time.sleep(0.033)  # ~30 FPS
                    
                except Exception as e:
                    print(f"   Frame capture error: {e}")
                    continue
            
            elapsed = time.time() - start_time
            fps = frame_count / elapsed
            print(f"✅ Dual streaming completed!")
            print(f"   - Duration: {elapsed:.1f}s")
            print(f"   - Total frames: {frame_count}")
            print(f"   - Average FPS: {fps:.1f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Dual streaming error: {e}")
            return False
        finally:
            if self.csi_camera:
                self.csi_camera.stop()
                self.csi_camera.close()
            if self.usb_camera:
                self.usb_camera.release()

    def run_all_tests(self):
        """Run comprehensive camera tests"""
        print("🚀 Starting GuardIt Camera Vision Tests")
        print("=" * 50)
        
        # Test 1: CSI Camera
        csi_result = self.test_csi_camera()
        print()
        
        # Test 2: USB Camera (try different device IDs)
        usb_result = False
        for device_id in [1, 0, 2]:
            print(f"Trying USB camera device {device_id}...")
            usb_result = self.test_usb_camera(device_id)
            if usb_result:
                break
            print()
        
        # Test 3: Dual camera streaming
        if csi_result and usb_result:
            print()
            dual_result = self.test_dual_camera_streaming(duration=5)
        else:
            dual_result = False
            print("⏭️  Skipping dual camera test (one or both cameras failed)")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 CAMERA TEST SUMMARY")
        print("=" * 50)
        print(f"CSI Camera (imx219):    {'✅ PASS' if csi_result else '❌ FAIL'}")
        print(f"USB Camera:             {'✅ PASS' if usb_result else '❌ FAIL'}")
        print(f"Dual Camera Streaming:  {'✅ PASS' if dual_result else '❌ FAIL'}")
        
        if csi_result and usb_result:
            print("\n🎉 All camera tests passed! Your vision system is ready!")
        else:
            print("\n⚠️  Some camera tests failed. Check connections and permissions.")
        
        return csi_result, usb_result, dual_result

if __name__ == "__main__":
    tester = CameraTestManager()
    tester.run_all_tests()

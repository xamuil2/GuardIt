#!/usr/bin/env python3
import cv2
import numpy as np
import traceback

def test_cameras():
    print("=== Camera Debug Test ===")
    
    # Test USB camera
    print("\n1. Testing USB camera (device 1)...")
    try:
        cap = cv2.VideoCapture(1, cv2.CAP_V4L2)
        print(f"Camera opened: {cap.isOpened()}")
        
        if cap.isOpened():
            # Set some basic properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            
            # Try to capture
            ret, frame = cap.read()
            print(f"Frame captured: {ret}")
            
            if ret and frame is not None:
                print(f"Frame shape: {frame.shape}")
                print(f"Frame dtype: {frame.dtype}")
                print(f"Frame min/max: {frame.min()}/{frame.max()}")
                print(f"Frame mean: {frame.mean():.2f}")
                
                # Check if frame is all black
                if frame.mean() < 1.0:
                    print("WARNING: Frame appears to be black!")
                else:
                    print("Frame has content")
                
                # Save test image
                cv2.imwrite('/home/guardit/Documents/GuardIt/raspberry-pi-iot/usb_debug.jpg', frame)
                print("USB test image saved")
                
                # Test JPEG encoding
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, 70]
                ret_encode, buffer = cv2.imencode('.jpg', frame, encode_params)
                if ret_encode:
                    print(f"JPEG encoding successful: {len(buffer)} bytes")
                else:
                    print("JPEG encoding failed!")
            else:
                print("Failed to capture frame")
            
            cap.release()
        else:
            print("Failed to open USB camera")
            
    except Exception as e:
        print(f"USB camera error: {e}")
        traceback.print_exc()
    
    # Test CSI camera
    print("\n2. Testing CSI camera (device 0)...")
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        print(f"Camera opened: {cap.isOpened()}")
        
        if cap.isOpened():
            # Set some basic properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            
            # Try to capture
            ret, frame = cap.read()
            print(f"Frame captured: {ret}")
            
            if ret and frame is not None:
                print(f"Frame shape: {frame.shape}")
                print(f"Frame dtype: {frame.dtype}")
                print(f"Frame min/max: {frame.min()}/{frame.max()}")
                print(f"Frame mean: {frame.mean():.2f}")
                
                # Check if frame is all black
                if frame.mean() < 1.0:
                    print("WARNING: Frame appears to be black!")
                else:
                    print("Frame has content")
                
                # Save test image
                cv2.imwrite('/home/guardit/Documents/GuardIt/raspberry-pi-iot/csi_debug.jpg', frame)
                print("CSI test image saved")
                
                # Test JPEG encoding
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, 70]
                ret_encode, buffer = cv2.imencode('.jpg', frame, encode_params)
                if ret_encode:
                    print(f"JPEG encoding successful: {len(buffer)} bytes")
                else:
                    print("JPEG encoding failed!")
            else:
                print("Failed to capture frame")
            
            cap.release()
        else:
            print("Failed to open CSI camera")
            
    except Exception as e:
        print(f"CSI camera error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_cameras()

#!/usr/bin/env python3
import cv2
import traceback

def test_usb_devices():
    print("=== USB Camera Device Test ===")
    
    usb_devices = [0, 1]  # USB camera shows on video0 and video1
    
    for device_id in usb_devices:
        print(f"\n🔍 Testing USB device {device_id} (/dev/video{device_id})...")
        try:
            cap = cv2.VideoCapture(device_id, cv2.CAP_V4L2)
            print(f"   Camera opened: {cap.isOpened()}")
            
            if cap.isOpened():
                # Get device capabilities
                backend = cap.getBackendName()
                print(f"   Backend: {backend}")
                
                # Try to get device info
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                fps = cap.get(cv2.CAP_PROP_FPS)
                fourcc = cap.get(cv2.CAP_PROP_FOURCC)
                
                print(f"   Default resolution: {int(width)}x{int(height)}")
                print(f"   Default FPS: {fps}")
                print(f"   FourCC: {int(fourcc)}")
                
                # Set test resolution
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                
                # Try to capture
                ret, frame = cap.read()
                print(f"   Frame captured: {ret}")
                
                if ret and frame is not None:
                    print(f"   Frame shape: {frame.shape}")
                    print(f"   Frame dtype: {frame.dtype}")
                    print(f"   Frame min/max: {frame.min()}/{frame.max()}")
                    print(f"   Frame mean: {frame.mean():.2f}")
                    
                    # Check if frame is valid
                    if frame.mean() < 1.0:
                        print("   ⚠️  WARNING: Frame appears to be black!")
                    else:
                        print("   ✅ Frame has content")
                    
                    # Save test image
                    filename = f'/home/guardit/Documents/GuardIt/raspberry-pi-iot/usb_device_{device_id}_test.jpg'
                    cv2.imwrite(filename, frame)
                    print(f"   💾 Test image saved: {filename}")
                    
                    # Test JPEG encoding
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, 70]
                    ret_encode, buffer = cv2.imencode('.jpg', frame, encode_params)
                    if ret_encode:
                        print(f"   📦 JPEG encoding successful: {len(buffer)} bytes")
                    else:
                        print("   ❌ JPEG encoding failed!")
                else:
                    print("   ❌ Failed to capture frame")
                
                cap.release()
                print(f"   🎯 Device {device_id}: {'WORKING' if ret and frame is not None else 'NOT WORKING'}")
            else:
                print(f"   ❌ Failed to open device {device_id}")
                
        except Exception as e:
            print(f"   💥 Error with device {device_id}: {e}")
            traceback.print_exc()
    
    print("\n" + "="*50)
    print("🎯 USB Camera Test Summary:")
    print("• Check which device IDs are working")
    print("• Look for 'WORKING' status above")
    print("• Update your server code to use the working device ID")

if __name__ == "__main__":
    test_usb_devices()

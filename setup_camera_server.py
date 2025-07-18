#!/usr/bin/env python3
"""
GuardIt Camera Server Setup Script
This script helps you set up and run the OpenCV camera server for GuardIt.
"""

import subprocess
import sys
import os
import socket

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def install_requirements():
    """Install required Python packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def check_camera():
    """Check if camera is available"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✅ Camera is available and working!")
            cap.release()
            return True
        else:
            print("❌ Camera is not available. Please check your camera connection.")
            return False
    except ImportError:
        print("❌ OpenCV not installed. Please run the setup again.")
        return False
    except Exception as e:
        print(f"❌ Error checking camera: {e}")
        return False

def start_server():
    """Start the camera server"""
    print("\n🚀 Starting GuardIt Camera Server...")
    local_ip = get_local_ip()
    print(f"📱 Your phone should connect to: {local_ip}:8090")
    print("📋 Make sure your phone and computer are on the same WiFi network")
    print("\n🔧 Server controls:")
    print("   - Press Ctrl+C to stop the server")
    print("   - Open http://localhost:8090 in your browser to test")
    print("\n" + "="*50)
    
    try:
        subprocess.run([sys.executable, "opencv_server.py"])
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")

def main():
    print("🔧 GuardIt Camera Server Setup")
    print("="*40)
    
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found!")
        return
    
    if not os.path.exists("opencv_server.py"):
        print("❌ opencv_server.py not found!")
        return
    
    print("1. Installing required packages...")
    if not install_requirements():
        return
    
    print("\n2. Checking camera availability...")
    if not check_camera():
        print("\n💡 Troubleshooting tips:")
        print("   - Make sure your camera is connected")
        print("   - Check if another app is using the camera")
        print("   - Try restarting your computer")
        return
    
    print("\n3. Starting camera server...")
    start_server()

if __name__ == "__main__":
    main() 
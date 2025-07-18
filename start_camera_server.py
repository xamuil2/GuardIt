#!/usr/bin/env python3
"""
Start the existing OpenCV camera server for GuardIt
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

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import flask
        import flask_cors
        import cv2
        import numpy
        print("✅ All required packages are installed!")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please install required packages:")
        print("pip install flask flask-cors opencv-python numpy ultralytics")
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
        os.chdir("OpenCV Testing")
        subprocess.run([sys.executable, "stream_server.py"])
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")

def main():
    print("🔧 GuardIt Camera Server Setup")
    print("="*40)
    
    if not os.path.exists("OpenCV Testing/stream_server.py"):
        print("❌ OpenCV Testing/stream_server.py not found!")
        return
    
    print("1. Checking dependencies...")
    if not check_dependencies():
        return
    
    print("\n2. Starting camera server...")
    start_server()

if __name__ == "__main__":
    main() 
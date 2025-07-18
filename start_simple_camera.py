#!/usr/bin/env python3
"""
Start the simple camera server for GuardIt
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

def main():
    print("🚀 GuardIt Simple Camera Server")
    print("="*40)
    
    if not os.path.exists("simple_camera_server.py"):
        print("❌ simple_camera_server.py not found!")
        return
    
    local_ip = get_local_ip()
    print(f"📱 Your phone should connect to: {local_ip}:8090")
    print(f"🌐 Open in Safari: http://{local_ip}:8090")
    print("📋 Make sure your phone and computer are on the same WiFi network")
    print("\n🔧 Server controls:")
    print("   - Press Ctrl+C to stop the server")
    print("   - Open http://localhost:8090 in your browser to test")
    print("\n" + "="*50)
    
    try:
        subprocess.run([sys.executable, "simple_camera_server.py"])
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")

if __name__ == "__main__":
    main() 
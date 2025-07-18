#!/usr/bin/env python3
"""
Get the current IP address for the camera feed
"""

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

if __name__ == "__main__":
    ip = get_local_ip()
    print(f"Your camera feed URL: http://{ip}:8090")
    print(f"Make sure the OpenCV server is running with: python3 start_camera_server.py") 
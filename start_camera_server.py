#!/usr/bin/env python3

import subprocess
import sys
import os
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def check_dependencies():
    try:
        import flask
        import flask_cors
        import cv2
        import numpy
        return True
    except ImportError as e:
        return False

def start_server():
    local_ip = get_local_ip()
    
    try:
        os.chdir("OpenCV Testing")
        subprocess.run([sys.executable, "stream_server.py"])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        pass

def main():
    if not os.path.exists("OpenCV Testing/stream_server.py"):
        return
    
    if not check_dependencies():
        return
    
    start_server()

if __name__ == "__main__":
    main() 
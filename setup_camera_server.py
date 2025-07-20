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

def install_requirements():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError as e:
        return False

def check_camera():
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.release()
            return True
        else:
            return False
    except ImportError:
        return False
    except Exception as e:
        return False

def start_server():
    local_ip = get_local_ip()
    
    try:
        subprocess.run([sys.executable, "opencv_server.py"])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        pass

def main():
    if not os.path.exists("requirements.txt"):
        return
    
    if not os.path.exists("opencv_server.py"):
        return
    
    if not install_requirements():
        return
    
    if not check_camera():
        return
    
    start_server()

if __name__ == "__main__":
    main() 
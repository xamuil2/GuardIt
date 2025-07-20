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

def main():
    if not os.path.exists("simple_camera_server.py"):
        return
    
    local_ip = get_local_ip()
    
    try:
        subprocess.run([sys.executable, "simple_camera_server.py"])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        pass

if __name__ == "__main__":
    main() 
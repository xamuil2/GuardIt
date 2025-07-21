import subprocess
import os
import sys
import time

def run_command(cmd, description):

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.stdout:
        if result.stderr:
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        return False

def main():
    
    if not run_command("which libcamera-still", "Checking if libcamera-still is available"):
        run_command("sudo apt update && sudo apt install -y libcamera-tools", "Installing libcamera-tools")
    
    if run_command("libcamera-hello --list-cameras", "Listing available cameras"):
    else:
    
    run_command("vcgencmd get_camera", "Getting camera info")
    
    if run_command("libcamera-still -o test_capture.jpg -t 1000", "Taking test photo"):
        if os.path.exists("test_capture.jpg"):
            size = os.path.getsize("test_capture.jpg")
            if size > 1000:
            else:
        else:
    else:
    
    if os.path.exists("/boot/config.txt"):
        with open("/boot/config.txt", "r") as f:
            config = f.read()
            if "camera_auto_detect=1" in config:
            else:
            
            if "start_x=1" in config:
            else:
            
            if "gpu_mem=" in config:
            else:
    else:
    
    run_command("ls -la /dev/video*", "Checking video devices")

if __name__ == "__main__":
    main()

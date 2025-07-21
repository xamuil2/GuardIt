import os
import sys
import subprocess
import time

def check_requirements():
    
    required_packages = [
        'smbus2', 'flask', 'RPi.GPIO'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        for pkg in missing_packages:
        return False
    
    return True

def get_pi_ip():
    
    try:
        result = subprocess.run(['python3', 'get_pi_ip.py'], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            return result.stdout
        else:
            return "Could not determine IP address"
    except Exception as e:
        return f"Error getting IP: {e}"

def main():
    
    if not check_requirements():
        sys.exit(1)
    
    ip_info = get_pi_ip()
    
    response = input("Start server now? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        time.sleep(1)
        
        try:
            subprocess.run(['python3', 'imu_wifi_server.py'], cwd=os.path.dirname(__file__))
        except KeyboardInterrupt:
        except Exception as e:
    else:

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
GuardIt Raspberry Pi Server Launcher
Easy-to-use script to start the IMU WiFi server with helpful information
"""

import os
import sys
import subprocess
import time

def check_requirements():
    """Check if required packages are installed"""
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
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print()
        print("Install with:")
        print(f"   pip3 install {' '.join(missing_packages)}")
        return False
    
    return True

def get_pi_ip():
    """Get Raspberry Pi IP address"""
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
    print("🛡️  GuardIt Raspberry Pi Server Launcher")
    print("=" * 50)
    print()
    
    # Check requirements
    print("🔍 Checking requirements...")
    if not check_requirements():
        sys.exit(1)
    print("✅ All requirements satisfied")
    print()
    
    # Show IP information
    print("📡 Network Information:")
    ip_info = get_pi_ip()
    print(ip_info)
    
    # Ask for confirmation
    print("🚀 Ready to start GuardIt IMU server!")
    print()
    response = input("Start server now? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        print()
        print("🔄 Starting server...")
        print("   Press Ctrl+C to stop")
        print()
        time.sleep(1)
        
        try:
            # Start the IMU server
            subprocess.run(['python3', 'imu_wifi_server.py'], cwd=os.path.dirname(__file__))
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        except Exception as e:
            print(f"\n❌ Error starting server: {e}")
    else:
        print("👋 Exiting without starting server")

if __name__ == "__main__":
    main()

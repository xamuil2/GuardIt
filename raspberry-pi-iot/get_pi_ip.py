#!/usr/bin/env python3
"""
Get Raspberry Pi IP Address for GuardIt iOS App
Simple script to get the Pi's IP address to configure in the iOS app
"""

import socket
import subprocess
import sys

def get_local_ip():
    """Get the local IP address of the Raspberry Pi"""
    try:
        # Method 1: Connect to a remote server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            # Method 2: Use hostname
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return None

def get_wifi_ip():
    """Get IP from WiFi interface specifically"""
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        if result.returncode == 0:
            ips = result.stdout.strip().split()
            # Return the first IP that's not localhost
            for ip in ips:
                if not ip.startswith('127.'):
                    return ip
    except Exception:
        pass
    return None

def main():
    print("🔍 Getting Raspberry Pi IP address for GuardIt iOS app...")
    print()
    
    # Try multiple methods
    local_ip = get_local_ip()
    wifi_ip = get_wifi_ip()
    
    if local_ip:
        print(f"📡 Local IP (Method 1): {local_ip}")
    
    if wifi_ip and wifi_ip != local_ip:
        print(f"📡 WiFi IP (Method 2): {wifi_ip}")
    
    # Determine the best IP to use
    recommended_ip = local_ip or wifi_ip
    
    if recommended_ip:
        print()
        print("✅ RECOMMENDED CONFIGURATION:")
        print(f"   IP Address: {recommended_ip}")
        print(f"   Port: 8080")
        print(f"   Full URL: http://{recommended_ip}:8080")
        print()
        print("📱 In your iOS app (IMU Screen):")
        print(f"   Enter IP: {recommended_ip}")
        print("   Or enter: {recommended_ip}:8080")
        print()
        print("🚀 To start the IMU server:")
        print("   python3 imu_wifi_server.py")
    else:
        print("❌ Could not determine IP address!")
        print("   Try running: ip addr show")
        print("   Or: ifconfig")
        sys.exit(1)

if __name__ == "__main__":
    main()

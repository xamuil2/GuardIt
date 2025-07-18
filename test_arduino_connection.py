#!/usr/bin/env python3
"""
Arduino Connection Test Script

This script helps test connectivity to your Arduino and identify which project is running.
It will test both port 80 and 8080 to see which one responds.

Usage:
    python test_arduino_connection.py [IP_ADDRESS]
    
Example:
    python test_arduino_connection.py 172.20.10.11
"""

import requests
import sys
import time
from urllib.parse import urljoin

def test_endpoint(url, timeout=3):
    """Test a specific endpoint"""
    try:
        print(f"Testing: {url}")
        response = requests.get(url, timeout=timeout)
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {response.text[:200]}...")
        return True, response.text
    except requests.exceptions.Timeout:
        print(f"❌ Timeout")
        return False, None
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection refused")
        return False, None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

def test_arduino_connection(ip_address):
    """Test Arduino connection on both ports"""
    print(f"🔍 Testing Arduino connection to {ip_address}")
    print("=" * 50)
    
    ports = [80, 8080]
    endpoints = ['/', '/status', '/imu', '/data', '/sensor']
    
    results = {}
    
    for port in ports:
        print(f"\n📡 Testing Port {port}")
        print("-" * 30)
        
        base_url = f"http://{ip_address}:{port}"
        port_results = {}
        
        for endpoint in endpoints:
            url = urljoin(base_url, endpoint)
            success, response = test_endpoint(url)
            port_results[endpoint] = {
                'success': success,
                'response': response
            }
            
            if success:
                print(f"🎉 Found working endpoint: {url}")
        
        results[port] = port_results
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 CONNECTION SUMMARY")
    print("=" * 50)
    
    working_ports = []
    for port, port_results in results.items():
        working_endpoints = [ep for ep, result in port_results.items() if result['success']]
        if working_endpoints:
            working_ports.append(port)
            print(f"✅ Port {port}: {len(working_endpoints)} endpoints working")
            for endpoint in working_endpoints:
                print(f"   - {endpoint}")
        else:
            print(f"❌ Port {port}: No endpoints responding")
    
    if working_ports:
        print(f"\n🎯 RECOMMENDATION:")
        print(f"Use IP: {ip_address}:{working_ports[0]}")
        print(f"Or just: {ip_address} (app will auto-detect port)")
    else:
        print(f"\n❌ NO CONNECTION FOUND")
        print("Check if Arduino is running and connected to the same network")
    
    return working_ports

def identify_arduino_project(response_text):
    """Try to identify which Arduino project is running based on response"""
    if not response_text:
        return "Unknown"
    
    response_lower = response_text.lower()
    
    if "guardit" in response_lower:
        return "GuardIt IMU Server (arduino/IMU_WiFi_Server.ino)"
    elif "accelerometer" in response_lower and "gps" in response_lower:
        return "LeanSensors Project (PlatformIO)"
    elif "mpu" in response_lower:
        return "MPU6050/MPU9250 Sensor Project"
    elif "wifi" in response_lower and "server" in response_lower:
        return "Generic WiFi Server"
    else:
        return "Unknown Arduino Project"

def main():
    # Get IP address from command line or use default
    if len(sys.argv) > 1:
        ip_address = sys.argv[1]
    else:
        ip_address = input("Enter Arduino IP address (e.g., 172.20.10.11): ").strip()
    
    if not ip_address:
        print("❌ No IP address provided")
        return
    
    print(f"🚀 Starting Arduino connection test...")
    print(f"📍 Target IP: {ip_address}")
    print(f"⏰ Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    working_ports = test_arduino_connection(ip_address)
    
    if working_ports:
        print(f"\n🔧 NEXT STEPS:")
        print(f"1. Use IP address: {ip_address}")
        print(f"2. The GuardIt app will automatically detect the correct port")
        print(f"3. If manual port needed, use: {ip_address}:{working_ports[0]}")
    else:
        print(f"\n🔧 TROUBLESHOOTING:")
        print(f"1. Check if Arduino is powered on")
        print(f"2. Verify both devices are on same network")
        print(f"3. Check Arduino Serial Monitor for IP address")
        print(f"4. Try uploading Arduino code again")

if __name__ == "__main__":
    main() 
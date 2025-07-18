#!/usr/bin/env python3
"""
Test script to verify Arduino IMU data transmission
This script will help debug why live sensor data isn't coming through
"""

import requests
import json
import time
from datetime import datetime

def test_arduino_connection(ip_address, port=80):
    """Test basic connection to Arduino"""
    base_url = f"http://{ip_address}:{port}"
    
    print(f"Testing connection to {base_url}")
    print("=" * 50)
    
    # Test 1: Server info (root endpoint)
    try:
        print("1. Testing server info endpoint...")
        response = requests.get(f"{base_url}/", timeout=5, headers={
            'Accept': 'application/json',
            'User-Agent': 'curl/7.68.0'
        })
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server info: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Server info failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Server info error: {e}")
        return False
    
    # Test 2: Status endpoint
    try:
        print("\n2. Testing status endpoint...")
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status error: {e}")
    
    # Test 3: IMU data endpoint
    try:
        print("\n3. Testing IMU data endpoint...")
        response = requests.get(f"{base_url}/imu", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ IMU data: {json.dumps(data, indent=2)}")
            
            # Validate data structure
            required_fields = ['ax', 'ay', 'az', 'gx', 'gy', 'gz', 'temp', 'alert', 'alert_type', 'timestamp']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"⚠️  Missing fields: {missing_fields}")
            else:
                print("✅ All required fields present")
                
            # Check data values
            if data['ax'] == 0 and data['ay'] == 0 and data['az'] == 0:
                print("⚠️  All acceleration values are 0 - sensor may not be working")
            else:
                print("✅ Acceleration data looks good")
                
        else:
            print(f"❌ IMU data failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ IMU data error: {e}")
    
    return True

def monitor_arduino_data(ip_address, port=80, duration=30):
    """Monitor Arduino data for a specified duration"""
    base_url = f"http://{ip_address}:{port}"
    
    print(f"\nMonitoring Arduino data for {duration} seconds...")
    print("=" * 50)
    
    start_time = time.time()
    data_count = 0
    last_timestamp = None
    
    try:
        while time.time() - start_time < duration:
            try:
                response = requests.get(f"{base_url}/imu", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    data_count += 1
                    
                    # Check if timestamp is changing (data is updating)
                    current_timestamp = data.get('timestamp', 0)
                    if last_timestamp is not None and current_timestamp == last_timestamp:
                        print(f"⚠️  Data not updating - same timestamp: {current_timestamp}")
                    else:
                        print(f"✅ Data {data_count}: {datetime.now().strftime('%H:%M:%S')} - "
                              f"Accel: ({data['ax']:.2f}, {data['ay']:.2f}, {data['az']:.2f}) "
                              f"Gyro: ({data['gx']:.2f}, {data['gy']:.2f}, {data['gz']:.2f}) "
                              f"Temp: {data['temp']:.1f}°C "
                              f"Alert: {data['alert']}")
                    
                    last_timestamp = current_timestamp
                else:
                    print(f"❌ Failed to get data: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print("⏰ Request timeout")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            time.sleep(1)  # Wait 1 second between requests
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    
    print(f"\nSummary: Received {data_count} data points in {duration} seconds")
    if data_count == 0:
        print("❌ No data received - check Arduino connection and sensor")
    elif data_count < duration * 0.8:  # Less than 80% of expected
        print("⚠️  Data reception rate is low - may indicate connection issues")
    else:
        print("✅ Data reception rate looks good")

def main():
    # Get Arduino IP from user
    ip_address = input("Enter Arduino IP address (default: 172.20.10.11): ").strip()
    if not ip_address:
        ip_address = "172.20.10.11"
    
    # Test both ports
    for port in [80, 8080]:
        print(f"\n{'='*60}")
        print(f"TESTING PORT {port}")
        print(f"{'='*60}")
        
        if test_arduino_connection(ip_address, port):
            print(f"\n✅ Connection successful on port {port}")
            
            # Ask if user wants to monitor data
            monitor = input(f"\nMonitor data on port {port} for 30 seconds? (y/n): ").strip().lower()
            if monitor in ['y', 'yes']:
                monitor_arduino_data(ip_address, port, 30)
            
            break
        else:
            print(f"❌ Connection failed on port {port}")
    else:
        print("\n❌ Failed to connect on both ports 80 and 8080")
        print("Please check:")
        print("1. Arduino is powered on and connected to WiFi")
        print("2. IP address is correct")
        print("3. Both devices are on the same network")
        print("4. No firewall blocking the connection")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime

def test_arduino_connection(ip_address, port=80):
    base_url = f"http://{ip_address}:{port}"
    
    try:
        response = requests.get(f"{base_url}/", timeout=5, headers={
            'Accept': 'application/json',
            'User-Agent': 'curl/7.68.0'
        })
        if response.status_code == 200:
            data = response.json()
        else:
            return False
    except Exception as e:
        return False
    
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
    except Exception as e:
        pass
    
    try:
        response = requests.get(f"{base_url}/imu", timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ['ax', 'ay', 'az', 'gx', 'gy', 'gz', 'temp', 'alert', 'alert_type', 'timestamp']
            missing_fields = [field for field in required_fields if field not in data]
            
            if data['ax'] == 0 and data['ay'] == 0 and data['az'] == 0:
                pass
                
        else:
            pass
    except Exception as e:
        pass
    
    return True

def monitor_arduino_data(ip_address, port=80, duration=30):
    base_url = f"http://{ip_address}:{port}"
    
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
                    
                    current_timestamp = data.get('timestamp', 0)
                    if last_timestamp is not None and current_timestamp == last_timestamp:
                        pass
                    
                    last_timestamp = current_timestamp
                else:
                    pass
                    
            except requests.exceptions.Timeout:
                pass
            except Exception as e:
                pass
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        pass

def main():
    ip_address = input("Enter Arduino IP address (default: 172.20.10.11): ").strip()
    if not ip_address:
        ip_address = "172.20.10.11"
    
    for port in [80, 8080]:
        if test_arduino_connection(ip_address, port):
            monitor = input(f"\nMonitor data on port {port} for 30 seconds? (y/n): ").strip().lower()
            if monitor in ['y', 'yes']:
                monitor_arduino_data(ip_address, port, 30)
            break
        else:
            pass
    else:
        pass

if __name__ == "__main__":
    main() 
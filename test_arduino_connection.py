#!/usr/bin/env python3

import requests
import sys
import time
from urllib.parse import urljoin

def test_endpoint(url, timeout=3):
    try:
        response = requests.get(url, timeout=timeout)
        return True, response.text
    except requests.exceptions.Timeout:
        return False, None
    except requests.exceptions.ConnectionError:
        return False, None
    except Exception as e:
        return False, None

def test_arduino_connection(ip_address):
    ports = [80, 8080]
    endpoints = ['/', '/status', '/imu', '/data', '/sensor']
    
    results = {}
    
    for port in ports:
        base_url = f"http://{ip_address}:{port}"
        port_results = {}
        
        for endpoint in endpoints:
            url = urljoin(base_url, endpoint)
            success, response = test_endpoint(url)
            port_results[endpoint] = {
                'success': success,
                'response': response
            }
        
        results[port] = port_results
    
    working_ports = []
    for port, port_results in results.items():
        working_endpoints = [ep for ep, result in port_results.items() if result['success']]
        if working_endpoints:
            working_ports.append(port)
    
    return working_ports

def identify_arduino_project(response_text):
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
    if len(sys.argv) > 1:
        ip_address = sys.argv[1]
    else:
        ip_address = input("Enter Arduino IP address (e.g., 172.20.10.11): ").strip()
    
    if not ip_address:
        return
    
    working_ports = test_arduino_connection(ip_address)

if __name__ == "__main__":
    main() 
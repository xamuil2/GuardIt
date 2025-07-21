import requests
import json
import time
import sys

def test_detection_endpoints(base_url):

    try:
        response = requests.get(f"{base_url}/detection/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
        else:
    except Exception as e:
    
    try:
        response = requests.post(
            f"{base_url}/detection/enable",
            json={"camera_type": "usb"},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
        else:
    except Exception as e:
    
    try:
        response = requests.post(f"{base_url}/detection/test", timeout=5)
        if response.status_code == 200:
            result = response.json()
        else:
    except Exception as e:
    
    try:
        response = requests.post(f"{base_url}/detection/disable", timeout=5)
        if response.status_code == 200:
            result = response.json()
        else:
    except Exception as e:

def test_main_server_notification(base_url):

    try:
        response = requests.post(
            f"{base_url}/notification/suspicious_activity",
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
        else:
    except Exception as e:

def main():

    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://10.103.186.99:8080"

    detection_url = base_url.replace(":8080", ":8081")
    test_detection_endpoints(detection_url)
    
    test_main_server_notification(base_url)

if __name__ == "__main__":
    main()

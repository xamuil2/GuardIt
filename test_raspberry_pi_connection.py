import requests
import sys
import time

def test_connection(ip_address):
    base_url = f"http://{ip_address}"

    try:
        response = requests.get(f"{base_url}/", timeout=5)
        
        if response.status_code == 200:
            try:
                data = response.json()
            except:
            return True
        else:
            return False
            
    except requests.exceptions.ConnectionError:
        return False
    except requests.exceptions.Timeout:
        return False
    except Exception as e:
        return False

def test_imu_endpoint(ip_address):
    base_url = f"http://{ip_address}"

    try:
        response = requests.get(f"{base_url}/imu", timeout=5)
        
        if response.status_code == 200:
            try:
                data = response.json()
            except:
            return True
        else:
            return False
            
    except Exception as e:
        return False

def test_camera_endpoint(ip_address):
    base_url = f"http://{ip_address}"

    try:
        response = requests.get(f"{base_url}/camera/usb", timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            return False
            
    except Exception as e:
        return False

def test_buzzer_endpoint(ip_address):
    base_url = f"http://{ip_address}"

    try:
        response = requests.post(f"{base_url}/buzzer", 
                               json={"frequency": 1000, "duration": 1000}, 
                               timeout=5)
        
        if response.status_code == 200:
            try:
                data = response.json()
            except:
            return True
        else:
            return False
            
    except Exception as e:
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
    ip_address = sys.argv[1]

    connection_ok = test_connection(ip_address)
    imu_ok = test_imu_endpoint(ip_address)
    camera_ok = test_camera_endpoint(ip_address)
    buzzer_ok = test_buzzer_endpoint(ip_address)

    if all([connection_ok, imu_ok, camera_ok, buzzer_ok]):
    else:
        sys.exit(1)

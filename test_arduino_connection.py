import requests
import sys
import time

def test_arduino_connection(ip_address, port=8080):
    base_url = f"http://{ip_address}:{port}"

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

def test_arduino_data(ip_address, port=8080):
        base_url = f"http://{ip_address}:{port}"

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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
        ip_address = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080

    connection_ok = test_arduino_connection(ip_address, port)
    data_ok = test_arduino_data(ip_address, port)

    if connection_ok and data_ok:
    else:
        sys.exit(1)

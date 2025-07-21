import requests
import sys
import time

def test_arduino_data(ip_address, port=8080):
    base_url = f"http://{ip_address}:{port}"

    try:
        response = requests.get(f"{base_url}/imu", timeout=5)
        
        if response.status_code == 200:
            try:
            data = response.json()
                return True
            except:
                return False
        else:
            return False
            
    except requests.exceptions.ConnectionError:
        return False
    except requests.exceptions.Timeout:
            return False
    except Exception as e:
        return False
    
def test_continuous_data(ip_address, port=8080, duration=10):
    base_url = f"http://{ip_address}:{port}"

    start_time = time.time()
    data_count = 0
    error_count = 0
    
        while time.time() - start_time < duration:
            try:
                response = requests.get(f"{base_url}/imu", timeout=2)
                if response.status_code == 200:
                    data_count += 1
                    else:
                error_count += 1
        except Exception as e:
            error_count += 1
            
        time.sleep(1)

    return data_count > 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
    ip_address = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    data_ok = test_arduino_data(ip_address, port)
    continuous_ok = test_continuous_data(ip_address, port, duration)

    if data_ok and continuous_ok:
    else:
        sys.exit(1)

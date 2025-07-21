import requests
import sys

def test_buzzer_endpoint(ip_address):
    base_url = f"http://{ip_address}"

    try:
        response = requests.get(f"{base_url}/", timeout=5)
        
        if response.status_code == 200:
            try:
                data = response.json()
            except:
        else:
            return False
            
    except requests.exceptions.ConnectionError:
        return False
    except requests.exceptions.Timeout:
        return False
    except Exception as e:
        return False

    buzzer_tests = [
        {"frequency": 1000, "duration": 2000, "description": "1kHz tone (2s)"},
        {"frequency": 2000, "duration": 1000, "description": "2kHz tone (1s)"},
        {"frequency": 500, "duration": 3000, "description": "500Hz tone (3s)"},
    ]
    
    success_count = 0
    
    for test in buzzer_tests:
        try:
            response = requests.post(f"{base_url}/buzzer", json=test, timeout=10)
            
            if response.status_code == 200:
                success_count += 1
            else:
                
        except Exception as e:

    if success_count == len(buzzer_tests):
        return True
    else:
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
    ip_address = sys.argv[1]
    success = test_buzzer_endpoint(ip_address)
    
    if not success:
        sys.exit(1)

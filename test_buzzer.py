import requests
import sys

def test_buzzer(ip_address, frequency=1000, duration=2000):
    base_url = f"http://{ip_address}"
    
    try:
        response = requests.post(f"{base_url}/buzzer", json={
            "frequency": frequency,
            "duration": duration
        })
        
        if response.status_code == 200:
            return True
        else:
            return False
            
    except requests.exceptions.RequestException as e:
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
    ip_address = sys.argv[1]
    frequency = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 2000

    success = test_buzzer(ip_address, frequency, duration)
    
    if success:
    else:
        sys.exit(1)

import socket
import subprocess
import sys

def get_local_ip():
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return None

def get_wifi_ip():
    
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        if result.returncode == 0:
            ips = result.stdout.strip().split()
            for ip in ips:
                if not ip.startswith('127.'):
                    return ip
    except Exception:
        pass
    return None

def main():
    
    local_ip = get_local_ip()
    wifi_ip = get_wifi_ip()
    
    if local_ip:
    
    if wifi_ip and wifi_ip != local_ip:
    
    recommended_ip = local_ip or wifi_ip
    
    if recommended_ip:
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

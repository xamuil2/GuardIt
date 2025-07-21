import subprocess
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, description):
    
    logger.info(f"{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        logger.info(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed: {e.stderr}")
        return False

def check_raspberry_pi():
    
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().strip('\x00')
            if 'Raspberry Pi' in model:
                logger.info(f"✓ Detected: {model}")
                return True
    except FileNotFoundError:
        pass
    
    logger.warning("⚠ Not running on Raspberry Pi - some features may not work")
    return False

def enable_interfaces():
    
    logger.info("Enabling I2C and camera interfaces...")
    
    if not run_command("which raspi-config", "Checking for raspi-config"):
        logger.warning("raspi-config not found - please enable I2C and camera manually")
        return False
    
    run_command("sudo raspi-config nonint do_i2c 0", "Enabling I2C")
    
    run_command("sudo raspi-config nonint do_camera 0", "Enabling camera")
    
    return True

def install_system_packages():
    
    packages = [
        "python3-dev",
        "python3-pip", 
        "python3-smbus",
        "i2c-tools",
        "libopencv-dev",
        "python3-opencv",
        "libjpeg-dev",
        "libpng-dev",
        "libtiff-dev",
        "libavcodec-dev",
        "libavformat-dev",
        "libswscale-dev",
        "libv4l-dev",
        "libxvidcore-dev",
        "libx264-dev"
    ]
    
    if not run_command("sudo apt update", "Updating package list"):
        return False
    
    package_list = " ".join(packages)
    return run_command(f"sudo apt install -y {package_list}", 
                      "Installing system packages")

def install_python_packages():
    
    logger.info("Installing Python packages...")
    
    run_command("python3 -m pip install --upgrade pip", "Upgrading pip")
    
    if os.path.exists("requirements.txt"):
        return run_command("python3 -m pip install -r requirements.txt", 
                          "Installing Python requirements")
    else:
        logger.error("requirements.txt not found")
        return False

def setup_user_permissions():
    
    import getpass
    username = getpass.getuser()
    
    logger.info("Setting up user permissions...")
    
    run_command(f"sudo usermod -a -G gpio {username}", 
                "Adding user to gpio group")
    run_command(f"sudo usermod -a -G i2c {username}", 
                "Adding user to i2c group")
    
    return True

def verify_installation():
    
    logger.info("Verifying installation...")
    
    if run_command("ls /dev/i2c-*", "Checking I2C devices"):
        logger.info("✓ I2C devices found")
    
    if run_command("ls /dev/video*", "Checking video devices"):
        logger.info("✓ Video devices found")
    
    test_imports = [
        "import RPi.GPIO",
        "import smbus2", 
        "import cv2",
        "import fastapi",
        "import uvicorn"
    ]
    
    for import_test in test_imports:
        try:
            exec(import_test)
            logger.info(f"✓ {import_test.split()[1]} import successful")
        except ImportError as e:
            logger.error(f"✗ {import_test.split()[1]} import failed: {e}")

def create_systemd_service():
    
    service_content = f
    
    service_path = "/etc/systemd/system/iot-device.service"
    
    try:
        with open("/tmp/iot-device.service", "w") as f:
            f.write(service_content)
        
        run_command("sudo mv /tmp/iot-device.service " + service_path,
                   "Creating systemd service")
        run_command("sudo systemctl daemon-reload", "Reloading systemd")
        run_command("sudo systemctl enable iot-device.service", 
                   "Enabling auto-start service")
        
        logger.info("✓ Systemd service created")
        logger.info("  Start service: sudo systemctl start iot-device")
        logger.info("  Stop service: sudo systemctl stop iot-device")
        logger.info("  View logs: sudo journalctl -u iot-device -f")
        
    except Exception as e:
        logger.error(f"Failed to create systemd service: {e}")

def main():
    
    logger.info("=== Raspberry Pi IoT Device Setup ===\n")
    
    if os.geteuid() == 0:
        logger.error("Please run this script as a regular user, not as root")
        sys.exit(1)
    
    is_pi = check_raspberry_pi()
    
    try:
        if is_pi:
            enable_interfaces()
        
        install_system_packages()
        install_python_packages()
        
        if is_pi:
            setup_user_permissions()
        
        verify_installation()
        
        response = input("\nCreate auto-start service? (y/N): ").lower()
        if response == 'y':
            create_systemd_service()
        
        logger.info("\n=== Setup completed successfully! ===")
        
        if is_pi:
            logger.info("\nNext steps:")
            logger.info("1. Reboot your Raspberry Pi: sudo reboot")
            logger.info("2. Test hardware: python3 tests/test_hardware.py")
            logger.info("3. Start server: python3 main.py")
            logger.info("4. Access web interface: http://your-pi-ip:8000")
        else:
            logger.info("\nFor development on non-Pi systems:")
            logger.info("1. Test what you can: python3 tests/test_hardware.py")
            logger.info("2. Start server: python3 main.py")
            logger.info("3. Access web interface: http://localhost:8000")
    
    except KeyboardInterrupt:
        logger.info("\nSetup interrupted by user")
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

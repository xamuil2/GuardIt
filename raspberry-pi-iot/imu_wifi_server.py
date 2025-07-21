#!/usr/bin/env python3
"""
GuardIt IMU WiFi Server - Python version of Arduino IMU_WiFi_Server.ino
Exact replication of Arduino logic for Raspberry Pi
"""

import smbus2
import time
import json
import math
import threading
import logging
from dataclasses import dataclass, asdict
from typing import Optional
from flask import Flask, jsonify, request, Response
import RPi.GPIO as GPIO

# Camera imports
import cv2
import numpy as np
import subprocess
import base64
import io
from PIL import Image
import os

# Object detection imports
from object_detector import GuardItPersonDetector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WiFi/Network Configuration (equivalent to Arduino WiFi)
WIFI_SSID = "Avnit"  # Same as Arduino
WIFI_PASSWORD = "hihihihi"  # Same as Arduino
SERVER_PORT = 8080  # Changed from 80 to avoid permission issues

# Network discovery and IP detection
import socket
import subprocess

# Hardware Configuration (matching Arduino defines)
MPU6050_ADDR = 0x68
MPU6050_ACCEL_XOUT_H = 0x3B
MPU6050_PWR_MGMT_1 = 0x6B

# Buzzer configuration (Arduino-style for maximum volume)
BUZZER_PIN = 21
BUZZER_FREQUENCY = 1000  # Alert frequency matching Arduino
ALERT_DURATION = 200     # 200ms beeps like Arduino

# RGB LED configuration (matching HARDWARE_PINOUT.md)
LED_RED_PIN = 18
LED_GREEN_PIN = 19
LED_BLUE_PIN = 20

# Alert thresholds (exactly matching Arduino)
FALL_THRESHOLD = 20.0
MOVEMENT_THRESHOLD = 5.0
DATA_INTERVAL = 100  # milliseconds, same as Arduino
NOTIFICATION_COOLDOWN = 2000  # 2 seconds between notifications

class RGBLEDController:
    """RGB LED controller for status indication"""
    
    def __init__(self, red_pin, green_pin, blue_pin):
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin
        self.red_pwm = None
        self.green_pwm = None
        self.blue_pwm = None
        
        # Setup GPIO pins
        GPIO.setup(self.red_pin, GPIO.OUT)
        GPIO.setup(self.green_pin, GPIO.OUT)
        GPIO.setup(self.blue_pin, GPIO.OUT)
        
        # Initialize PWM for smooth color control
        self.red_pwm = GPIO.PWM(self.red_pin, 1000)
        self.green_pwm = GPIO.PWM(self.green_pin, 1000)
        self.blue_pwm = GPIO.PWM(self.blue_pin, 1000)
        
        # Start with LEDs off
        self.red_pwm.start(0)
        self.green_pwm.start(0)
        self.blue_pwm.start(0)
    
    def set_color(self, red, green, blue):
        """Set RGB color (0-100 for each channel)"""
        self.red_pwm.ChangeDutyCycle(red)
        self.green_pwm.ChangeDutyCycle(green)
        self.blue_pwm.ChangeDutyCycle(blue)
    
    def red(self):
        """Set LED to red (movement/alert detected)"""
        self.set_color(100, 0, 0)
    
    def green(self):
        """Set LED to green (normal operation)"""
        self.set_color(0, 100, 0)
    
    def blue(self):
        """Set LED to blue"""
        self.set_color(0, 0, 100)
    
    def off(self):
        """Turn off LED"""
        self.set_color(0, 0, 0)
    
    def cleanup(self):
        """Cleanup PWM"""
        if self.red_pwm:
            self.red_pwm.stop()
        if self.green_pwm:
            self.green_pwm.stop()
        if self.blue_pwm:
            self.blue_pwm.stop()

class MaxVolumeBuzzer:
    """Maximum volume buzzer using 100% duty cycle PWM"""
    
    def __init__(self, pin, frequency=2000):
        self.pin = pin
        self.frequency = frequency
        self.pwm = None
        self.is_active = False
        
    def start_tone(self):
        """Start continuous tone at maximum volume (100% duty cycle)"""
        if not self.is_active:
            self.pwm = GPIO.PWM(self.pin, self.frequency)
            self.pwm.start(50)  # 100% duty cycle for maximum volume
            self.is_active = True
            
    def stop_tone(self):
        """Stop the tone"""
        if self.is_active and self.pwm:
            self.pwm.stop()
            self.pwm = None
            self.is_active = False
    
    def beep(self, duration_ms):
        """Generate a beep for specified duration"""
        self.start_tone()
        time.sleep(duration_ms / 1000.0)
        self.stop_tone()
    
    def cleanup(self):
        """Cleanup PWM"""
        self.stop_tone()

@dataclass
class IMUData:
    """IMU data structure exactly matching Arduino struct"""
    ax: float = 0.0
    ay: float = 0.0
    az: float = 0.0
    gx: float = 0.0
    gy: float = 0.0
    gz: float = 0.0
    temp: float = 0.0
    alert: bool = False
    alertType: str = ""

class CameraManager:
    """Camera manager for USB and CSI cameras with object detection"""
    
    def __init__(self):
        self.csi_available = False
        self.usb_available = False
        self.usb_device_id = None
        self.streaming = False
        self.usb_cap = None
        # Threading for background frame capture (USB)
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.capture_thread = None
        self.capture_running = False
        # Threading for CSI camera
        self.csi_streaming = False
        self.latest_csi_frame = None
        self.csi_frame_lock = threading.Lock()
        self.csi_capture_thread = None
        self.csi_capture_running = False
        
        # Object detection
        self.detector = None
        self.detection_enabled = False
        self.last_detection_alert = 0
        self.detection_callback = None  # Callback function for detection alerts
        
        self._detect_cameras()
        self._initialize_detector()
    
    def _initialize_detector(self):
        """Initialize object detection"""
        try:
            self.detector = GuardItPersonDetector()
            logger.info("✅ Object detection initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize object detection: {e}")
            self.detector = None
    
    def _detect_cameras(self):
        """Detect available cameras"""
        logger.info("🔍 Detecting cameras...")
        
        # Test CSI camera with libcamera
        try:
            result = subprocess.run(
                ["libcamera-hello", "--list-cameras"], 
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and ("imx219" in result.stdout or "Camera" in result.stdout):
                self.csi_available = True
                logger.info("✅ CSI Camera detected")
            else:
                logger.warning("❌ CSI Camera not detected")
        except Exception as e:
            logger.warning(f"❌ CSI Camera detection failed: {e}")
        
        # Test USB cameras
        for device_id in [0, 1, 2]:
            cap = cv2.VideoCapture(device_id, cv2.CAP_V4L2)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    self.usb_available = True
                    self.usb_device_id = device_id
                    logger.info(f"✅ USB Camera detected on device {device_id}")
                    cap.release()
                    break
            cap.release()
        
        if not self.usb_available:
            logger.warning("❌ No USB Camera detected")
    
    def _background_capture(self):
        """Background thread to continuously capture frames"""
        print("🎥 Background camera capture started")
        while self.capture_running and self.usb_cap:
            try:
                # Clear buffer and get fresh frame
                for _ in range(2):
                    self.usb_cap.grab()
                ret, frame = self.usb_cap.retrieve()
                
                if ret and frame is not None:
                    # Encode frame immediately
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 15])
                    
                    with self.frame_lock:
                        self.latest_frame = buffer.tobytes()
                
                time.sleep(0.02)  # ~50fps capture rate
            except Exception as e:
                print(f"Background capture error: {e}")
                time.sleep(0.1)
        print("🛑 Background camera capture stopped")
    
    def _background_usb_capture(self):
        """Background thread for USB camera capture using OpenCV with object detection"""
        print("🎥 Background USB capture started")
        
        cap = cv2.VideoCapture(self.usb_device_id, cv2.CAP_V4L2)
        try:
            # Optimize camera settings for maximum speed
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            frame_count = 0
            detection_interval = 10  # Process every 10th frame for detection
            
            while self.capture_running and cap.isOpened():
                try:
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # Clear buffer to get latest frame only (convert float to int)
                        buffer_size = int(cap.get(cv2.CAP_PROP_BUFFERSIZE))
                        for _ in range(max(1, buffer_size)):  # Ensure at least 1 iteration
                            cap.grab()
                        
                        # Object detection (every Nth frame to reduce CPU load)
                        detection_triggered = False
                        processed_frame = frame
                        
                        if (self.detection_enabled and self.detector and 
                            frame_count % detection_interval == 0):
                            try:
                                detection_triggered, processed_frame = self.detector.process_detection(frame)
                                
                                if detection_triggered and self.detection_callback:
                                    # Trigger detection alert
                                    self.detection_callback("suspicious_activity")
                                    print("🚨 PERSON DETECTED - Suspicious activity alert triggered!")
                            
                            except Exception as e:
                                print(f"Detection processing error: {e}")
                        
                        # Use processed frame (with detection boxes if enabled)
                        frame_to_encode = processed_frame if self.detection_enabled else frame
                        
                        # Ultra-fast JPEG compression (quality 20)
                        _, buffer = cv2.imencode('.jpg', frame_to_encode, [cv2.IMWRITE_JPEG_QUALITY, 20])
                        
                        with self.frame_lock:
                            self.latest_frame = buffer.tobytes()
                        
                        frame_count += 1
                    
                    time.sleep(0.008)  # ~130 FPS theoretical max
                except Exception as e:
                    print(f"USB capture error: {e}")
                    time.sleep(0.1)
        
        except Exception as e:
            print(f"USB background capture failed: {e}")
        finally:
            if cap.isOpened():
                cap.release()
        
        print("🛑 Background USB capture stopped")
    
    def _background_csi_capture(self):
        """Background thread for CSI camera capture using libcamera-vid"""
        print("🎥 Background CSI capture started")
        
        # Use libcamera-vid for continuous streaming instead of libcamera-still
        cmd = [
            "libcamera-vid",
            "-o", "-",  # Output to stdout
            "-t", "0",  # Run indefinitely
            "--width", "160",
            "--height", "120",
            "--framerate", "10",  # 10 FPS target
            "--codec", "mjpeg",  # MJPEG for individual frame extraction
            "-n",  # No preview
            "--flush"  # Flush frames immediately
        ]
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            frame_buffer = b""
            while self.csi_capture_running and process.poll() is None:
                try:
                    # Read data in chunks
                    chunk = process.stdout.read(1024)
                    if not chunk:
                        break
                    
                    frame_buffer += chunk
                    
                    # Look for JPEG markers (FFD8 start, FFD9 end)
                    start_marker = b'\xff\xd8'
                    end_marker = b'\xff\xd9'
                    
                    start_idx = frame_buffer.find(start_marker)
                    if start_idx != -1:
                        end_idx = frame_buffer.find(end_marker, start_idx)
                        if end_idx != -1:
                            # Extract complete JPEG frame
                            jpeg_frame = frame_buffer[start_idx:end_idx + 2]
                            
                            with self.csi_frame_lock:
                                self.latest_csi_frame = jpeg_frame
                            
                            # Remove processed frame from buffer
                            frame_buffer = frame_buffer[end_idx + 2:]
                    
                    # Prevent buffer from growing too large
                    if len(frame_buffer) > 100000:  # 100KB limit
                        frame_buffer = frame_buffer[-50000:]  # Keep last 50KB
                        
                except Exception as e:
                    print(f"CSI capture error: {e}")
                    time.sleep(0.1)
            
            # Cleanup process
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=2)
                
        except Exception as e:
            print(f"CSI background capture failed: {e}")
        
        print("🛑 Background CSI capture stopped")
    
    def start_streaming(self):
        """Start background USB streaming"""
        if self.streaming:
            return True
            
        self.capture_running = True
        self.capture_thread = threading.Thread(target=self._background_usb_capture, daemon=True)
        self.capture_thread.start()
        self.streaming = True
        print("✅ USB streaming started")
        return True
    
    def stop_streaming(self):
        """Stop background USB streaming"""
        if not self.streaming:
            return
            
        self.capture_running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=3)
        self.streaming = False
        print("🛑 USB streaming stopped")
    
    def get_latest_frame(self):
        """Get latest USB frame if available"""
        if not self.streaming:
            # Fallback to single capture if streaming not active
            return self.capture_usb_image(width=160, height=120)
        
        with self.frame_lock:
            if self.latest_frame:
                return self.latest_frame
        
        return None
    
    def start_csi_streaming(self):
        """Start background CSI streaming"""
        if self.csi_streaming:
            return True
            
        self.csi_capture_running = True
        self.csi_capture_thread = threading.Thread(target=self._background_csi_capture, daemon=True)
        self.csi_capture_thread.start()
        self.csi_streaming = True
        print("✅ CSI streaming started")
        return True
    
    def stop_csi_streaming(self):
        """Stop background CSI streaming"""
        if not self.csi_streaming:
            return
            
        self.csi_capture_running = False
        if self.csi_capture_thread and self.csi_capture_thread.is_alive():
            self.csi_capture_thread.join(timeout=3)
        self.csi_streaming = False
        print("🛑 CSI streaming stopped")
    
    def get_csi_frame(self):
        """Get latest CSI frame if available"""
        if not self.csi_streaming:
            # Fallback to single capture if streaming not active
            return self.capture_csi_image(width=160, height=120)
        
        with self.csi_frame_lock:
            if self.latest_csi_frame:
                return self.latest_csi_frame
        
        return None
    
    def capture_csi_image(self, width=640, height=480):
        """Capture image from CSI camera using libcamera with ultra-low latency"""
        if not self.csi_available:
            return None, "CSI camera not available"
        
        # Use temp file but with optimizations for speed
        output_path = f"/tmp/csi_fast_{int(time.time() * 1000)}.jpg"
        
        try:
            # Ultra-fast CSI capture optimizations:
            # 1. Reduce capture time to 50ms (was 1000ms)
            # 2. Use smaller resolution for speed
            # 3. Reduce timeout to 3 seconds
            # 4. Use ultra-low quality for speed
            fast_width = min(width, 320)  # Cap at 320 for speed
            fast_height = min(height, 240)  # Cap at 240 for speed
            
            result = subprocess.run([
                "libcamera-still",
                "-o", output_path,
                "-t", "50",  # Ultra-fast 50ms capture (was 1000ms)
                "--width", str(fast_width),
                "--height", str(fast_height),
                "-n",  # No preview
                "--quality", "15"  # Ultra-low quality for speed
            ], capture_output=True, text=True, timeout=3)  # 3s timeout (was 10s)
            
            if result.returncode == 0 and os.path.exists(output_path):
                # Fast file read and cleanup
                with open(output_path, 'rb') as f:
                    image_data = f.read()
                os.remove(output_path)  # Immediate cleanup
                
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                return image_b64, None
            else:
                # Cleanup on failure
                if os.path.exists(output_path):
                    os.remove(output_path)
                return None, f"libcamera-still failed: {result.stderr}"
        
        except subprocess.TimeoutExpired:
            # Cleanup on timeout
            if os.path.exists(output_path):
                os.remove(output_path)
            return None, "CSI camera capture timed out (3s)"
        except Exception as e:
            # Cleanup on error
            if os.path.exists(output_path):
                os.remove(output_path)
            return None, f"CSI capture error: {e}"
    
    def capture_usb_image(self, width=640, height=480):
        """Capture image from USB camera using OpenCV"""
        if not self.usb_available:
            return None, "USB camera not available"
        
        cap = cv2.VideoCapture(self.usb_device_id, cv2.CAP_V4L2)
        try:
            # Optimize camera settings for speed
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce latency
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            
            # Capture frame
            ret, frame = cap.read()
            if ret and frame is not None:
                # Convert to JPEG with ultra-low quality for speed
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 20])
                image_b64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
                return image_b64, None
            else:
                return None, "Failed to capture USB camera frame"
        
        except Exception as e:
            return None, f"USB capture error: {e}"
        finally:
            cap.release()
    
    def start_usb_streaming(self):
        """Start USB camera streaming with background capture"""
        if not self.usb_available:
            return False
        
        if self.usb_cap is None:
            self.usb_cap = cv2.VideoCapture(self.usb_device_id, cv2.CAP_V4L2)
            # Ultra-fast streaming - tiny resolution for maximum speed
            self.usb_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
            self.usb_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
            self.usb_cap.set(cv2.CAP_PROP_FPS, 60)  # Request higher FPS
            # Reduce buffer size to minimize latency
            self.usb_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            # Set MJPEG format for better performance
            self.usb_cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        
        self.streaming = True
        
        # Start background capture thread
        if not self.capture_running:
            self.capture_running = True
            self.capture_thread = threading.Thread(target=self._background_capture, daemon=True)
            self.capture_thread.start()
        
        return True
    
    def stop_usb_streaming(self):
        """Stop USB camera streaming"""
        self.streaming = False
        self.capture_running = False
        
        # Wait for capture thread to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        
        if self.usb_cap:
            self.usb_cap.release()
            self.usb_cap = None
        
        with self.frame_lock:
            self.latest_frame = None
    
    def get_usb_frame(self):
        """Get latest frame from background capture thread"""
        if not self.streaming:
            return None
        
        with self.frame_lock:
            if self.latest_frame:
                # Convert to base64 for compatibility
                frame_b64 = base64.b64encode(self.latest_frame).decode('utf-8')
                return frame_b64
        return None
    
    def get_camera_status(self):
        """Get camera status"""
        return {
            'csi_available': self.csi_available,
            'usb_available': self.usb_available,
            'usb_device_id': self.usb_device_id,
            'streaming': self.streaming,
            'detection_enabled': self.detection_enabled,
            'detector_status': self.detector.get_status() if self.detector else None
        }
    
    def enable_detection(self):
        """Enable object detection"""
        if self.detector:
            self.detection_enabled = True
            self.detector.enable_detection()
            print("✅ Object detection enabled")
            return True
        else:
            print("❌ Object detector not available")
            return False
    
    def disable_detection(self):
        """Disable object detection"""
        self.detection_enabled = False
        if self.detector:
            self.detector.disable_detection()
        print("🛑 Object detection disabled")
    
    def set_detection_callback(self, callback):
        """Set callback function for detection alerts"""
        self.detection_callback = callback
    
    def set_detection_model(self, model_name):
        """Switch detection model"""
        if self.detector:
            return self.detector.set_model(model_name)
        return False
    
    def cleanup(self):
        """Cleanup camera resources"""
        self.stop_streaming()  # Stop USB streaming
        self.stop_csi_streaming()  # Stop CSI streaming
        self.capture_running = False
        self.csi_capture_running = False

class GuardItIMUServer:
    """Python equivalent of Arduino IMU WiFi Server"""
    
    def __init__(self):
        # Arduino equivalent variables
        self.current_data = IMUData()
        self.last_data_time = 0
        self.fall_detected = False
        self.movement_detected = False
        self.last_alert_time = 0
        self.last_notification_time = 0  # Prevent notification spam
        self.last_hardware_trigger_time = 0  # Track when LED/buzzer were triggered
        self.start_time = time.time()
        
        # Hardware components
        self.bus = None
        self.buzzer = None
        self.led = None
        self.camera = None
        self.running = False
        
        # Flask app (equivalent to Arduino WebServer)
        self.app = Flask(__name__)
        self.setup_routes()
        
        print("GuardIt IMU WiFi Server Starting...")
        
        # Initialize hardware
        self.init_gpio()
        
        # Initialize camera
        self.camera = CameraManager()
        
        # Set detection callback to trigger alerts
        if self.camera:
            self.camera.set_detection_callback(self.handle_detection_alert)
        
        if not self.init_mpu6050():
            print("Failed to initialize MPU6050!")
            raise Exception("MPU6050 initialization failed")
        
        # Start data reading thread (equivalent to Arduino loop())
        self.running = True
        self.data_thread = threading.Thread(target=self.main_loop, daemon=True)
        self.data_thread.start()
        
        print("HTTP server ready")
        print(f"Server Port: {SERVER_PORT}")
        print("Ready to receive connections from GuardIt app!")
    
    def init_gpio(self):
        """Initialize GPIO for buzzer and RGB LED"""
        try:
            # Clean up any previous GPIO state
            try:
                GPIO.cleanup()
            except Exception:
                pass  # Ignore cleanup errors if GPIO wasn't previously initialized
            
            # Set GPIO mode and disable warnings
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup buzzer pin
            GPIO.setup(BUZZER_PIN, GPIO.OUT)
            GPIO.output(BUZZER_PIN, GPIO.LOW)
            
            # Initialize maximum volume buzzer
            self.buzzer = MaxVolumeBuzzer(BUZZER_PIN, BUZZER_FREQUENCY)
            
            # Initialize RGB LED controller
            self.led = RGBLEDController(LED_RED_PIN, LED_GREEN_PIN, LED_BLUE_PIN)
            
            # Start with green LED (normal operation)
            self.led.green()
            
            logger.info("✅ GPIO initialized with buzzer and RGB LED")
            
        except Exception as e:
            logger.error(f"❌ GPIO initialization failed: {e}")
            # Don't raise exception, continue without GPIO
            print(f"⚠️  Warning: GPIO initialization failed: {e}")
            print("📱 Server will continue without hardware control")
    
    def init_mpu6050(self) -> bool:
        """Initialize MPU6050 - exact Arduino equivalent"""
        try:
            self.bus = smbus2.SMBus(1)  # I2C bus 1
            
            # Arduino: Wire.beginTransmission + Wire.write + Wire.endTransmission
            self.bus.write_byte_data(MPU6050_ADDR, MPU6050_PWR_MGMT_1, 0)
            
            # Verify sensor is responding
            who_am_i = self.bus.read_byte_data(MPU6050_ADDR, 0x75)
            if who_am_i not in [0x68, 0x70, 0x71, 0x73]:
                print("MPU6050 not found!")
                return False
            
            print("MPU6050 initialized successfully")
            return True
            
        except Exception as e:
            print(f"MPU6050 initialization error: {e}")
            return False
    
    def setup_routes(self):
        """Setup server routes - exact Arduino equivalent"""
        
        @self.app.route("/", methods=["GET", "OPTIONS"])
        def root():
            if request.method == "OPTIONS":
                return self.handle_cors()
            return jsonify(self.get_server_info())
        
        @self.app.route("/status", methods=["GET"])
        def status():
            return jsonify(self.get_status_info())
        
        @self.app.route("/imu", methods=["GET"])
        def imu():
            return jsonify(self.get_imu_data_json())
        
        @self.app.route("/data", methods=["GET"])
        def data():
            return jsonify(self.get_imu_data_json())
        
        @self.app.route("/sensor", methods=["GET"])
        def sensor():
            return jsonify(self.get_imu_data_json())
        
        # Camera endpoints
        @self.app.route("/camera", methods=["GET"])
        def camera_status():
            return jsonify(self.get_camera_status())
        
        @self.app.route("/camera/csi", methods=["GET"])
        def capture_csi():
            width = request.args.get('width', 640, type=int)
            height = request.args.get('height', 480, type=int)
            return jsonify(self.get_csi_image(width, height))
        
        @self.app.route("/camera/usb", methods=["GET"])
        def capture_usb():
            width = request.args.get('width', 640, type=int)
            height = request.args.get('height', 480, type=int)
            return jsonify(self.get_usb_image(width, height))
        
        @self.app.route("/camera/both", methods=["GET"])
        def capture_both():
            width = request.args.get('width', 640, type=int)
            height = request.args.get('height', 480, type=int)
            return jsonify(self.get_both_images(width, height))
        
        @self.app.route("/stream/start", methods=["POST"])
        def start_stream():
            return jsonify(self.start_camera_stream())
        
        @self.app.route("/stream/stop", methods=["POST"])
        def stop_stream():
            return jsonify(self.stop_camera_stream())
        
        @self.app.route("/stream/frame", methods=["GET"])
        def get_stream_frame():
            return jsonify(self.get_stream_frame())
        
        @self.app.route("/stream/fast", methods=["GET"])
        def get_fast_stream():
            return self.get_fast_stream_response()
        
        @self.app.route("/stream/raw", methods=["GET"])
        def get_raw_stream():
            return self.get_raw_stream_response()
        
        # Object detection endpoints
        @self.app.route("/detection/enable", methods=["POST"])
        def enable_detection():
            return jsonify(self.enable_object_detection())
        
        @self.app.route("/detection/disable", methods=["POST"])
        def disable_detection():
            return jsonify(self.disable_object_detection())
        
        @self.app.route("/detection/status", methods=["GET"])
        def detection_status():
            return jsonify(self.get_detection_status())
        
        @self.app.route("/detection/model", methods=["POST"])
        def set_detection_model():
            model_name = request.json.get('model', 'hog') if request.json else 'hog'
            return jsonify(self.set_detection_model(model_name))
        
        @self.app.after_request
        def after_request(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            return response
    
    def handle_cors(self):
        """Handle CORS preflight - Arduino equivalent"""
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    def get_local_ip(self):
        """Get the local IP address of the Raspberry Pi"""
        try:
            # Connect to a remote server to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            try:
                # Fallback method using hostname
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "192.168.1.100"  # Default fallback
    
    def get_server_info(self) -> dict:
        """Get server info - exact Arduino equivalent"""
        local_ip = self.get_local_ip()
        return {
            "name": "GuardIt IMU Server",
            "version": "1.0.0",
            "type": "raspberry-pi",
            "ip": local_ip,
            "port": SERVER_PORT,
            "status": "running",
            "endpoints": ["/status", "/imu", "/data", "/sensor", "/camera", "/camera/csi", "/camera/usb", "/camera/both", "/stream/start", "/stream/stop", "/stream/frame", "/stream/fast", "/stream/raw", "/detection/enable", "/detection/disable", "/detection/status", "/detection/model"],
            "camera_status": self.camera.get_camera_status() if self.camera else {}
        }
    
    def get_status_info(self) -> dict:
        """Get status info - Arduino equivalent"""
        local_ip = self.get_local_ip()
        return {
            "connected": True,
            "ip": local_ip,
            "rssi": -50,  # Mock WiFi signal strength
            "uptime": int(time.time() - self.start_time),
            "last_data_time": self.last_data_time
        }
    
    def get_imu_data_json(self) -> dict:
        """Get IMU data as JSON - exact Arduino equivalent"""
        data_dict = asdict(self.current_data)
        data_dict["timestamp"] = int(time.time() * 1000)  # milliseconds like Arduino
        return data_dict
    
    def get_camera_status(self) -> dict:
        """Get camera status"""
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        status = self.camera.get_camera_status()
        return {
            "camera_status": status,
            "available_endpoints": {
                "csi_capture": status['csi_available'],
                "usb_capture": status['usb_available'],
                "dual_capture": status['csi_available'] and status['usb_available'],
                "usb_streaming": status['usb_available']
            }
        }
    
    def get_csi_image(self, width=640, height=480) -> dict:
        """High-performance CSI camera image capture"""
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        start_time = time.time()
        
        try:
            # Ensure CSI streaming is active
            if not self.camera.csi_streaming:
                self.camera.start_csi_streaming()
                time.sleep(0.5)  # Allow streaming to initialize
            
            # Get latest frame from background thread
            frame_data = self.camera.get_csi_frame()
            
            if frame_data:
                # Encode frame to base64 for JSON response
                image_b64 = base64.b64encode(frame_data).decode('utf-8')
                response_time = round((time.time() - start_time) * 1000, 1)
                
                print(f"🎥 CSI frame delivered - Size: {len(frame_data)/1024:.1f}KB, Time: {response_time}ms")
                
                return {
                    "success": True,
                    "camera": "csi",
                    "image": image_b64,
                    "format": "jpeg",
                    "width": width,
                    "height": height,
                    "timestamp": int(time.time() * 1000),
                    "response_time_ms": response_time,
                    "streaming": True
                }
            else:
                return {"error": "No CSI frame available", "camera": "csi"}
                
        except Exception as e:
            return {"error": str(e), "camera": "csi"}
    
    def get_usb_image(self, width=640, height=480) -> dict:
        """High-performance USB camera image capture"""
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        start_time = time.time()
        
        try:
            # Ensure USB streaming is active
            if not self.camera.streaming:
                self.camera.start_streaming()
                time.sleep(0.3)  # Allow streaming to initialize
            
            # Get latest frame from background thread
            frame_data = self.camera.get_latest_frame()
            
            if frame_data:
                # Encode frame to base64 for JSON response
                image_b64 = base64.b64encode(frame_data).decode('utf-8')
                response_time = round((time.time() - start_time) * 1000, 1)
                
                print(f"🎥 USB frame delivered - Size: {len(frame_data)/1024:.1f}KB, Time: {response_time}ms")
                
                return {
                    "success": True,
                    "camera": "usb",
                    "image": image_b64,
                    "format": "jpeg",
                    "width": width,
                    "height": height,
                    "timestamp": int(time.time() * 1000),
                    "response_time_ms": response_time,
                    "streaming": True
                }
            else:
                return {"error": "No USB frame available", "camera": "usb"}
                
        except Exception as e:
            return {"error": str(e), "camera": "usb"}
    
    def get_both_images(self, width=640, height=480) -> dict:
        """Capture from both cameras"""
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        result = {"timestamp": int(time.time() * 1000), "cameras": {}}
        
        # Capture CSI
        if self.camera.csi_available:
            csi_image, csi_error = self.camera.capture_csi_image(width, height)
            if csi_error:
                result["cameras"]["csi"] = {"error": csi_error}
            else:
                result["cameras"]["csi"] = {
                    "success": True,
                    "image": csi_image,
                    "format": "jpeg",
                    "width": width,
                    "height": height
                }
        
        # Capture USB
        if self.camera.usb_available:
            usb_image, usb_error = self.camera.capture_usb_image(width, height)
            if usb_error:
                result["cameras"]["usb"] = {"error": usb_error}
            else:
                result["cameras"]["usb"] = {
                    "success": True,
                    "image": usb_image,
                    "format": "jpeg",
                    "width": width,
                    "height": height
                }
        
        return result
    
    def start_camera_stream(self) -> dict:
        """Start camera streaming"""
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        if self.camera.start_streaming():  # Use the new method name
            return {"success": True, "message": "USB camera streaming started"}
        else:
            return {"error": "Failed to start USB camera streaming"}
    
    def stop_camera_stream(self) -> dict:
        """Stop camera streaming"""
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        self.camera.stop_streaming()  # Use the new method name
        return {"success": True, "message": "Camera streaming stopped"}
    
    def get_stream_frame(self) -> dict:
        """Get current stream frame"""
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        if not self.camera.streaming:
            return {"error": "Streaming not active. Call /stream/start first"}
        
        frame = self.camera.get_usb_frame()
        if frame:
            return {
                "success": True,
                "frame": frame,
                "format": "jpeg",
                "timestamp": int(time.time() * 1000)
            }
        else:
            return {"error": "Failed to capture frame"}
    
    def get_fast_stream_response(self):
        """Get raw stream frame for faster performance"""
        if not self.camera or not self.camera.streaming:
            return jsonify({"error": "Streaming not active"})
        
        frame = self.camera.get_usb_frame()
        if frame:
            # Return minimal response for speed
            response = jsonify({"f": frame, "t": int(time.time() * 1000)})
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        else:
            return jsonify({"error": "Failed to capture frame"})
    
    def get_raw_stream_response(self):
        """Get raw JPEG bytes from background thread for maximum speed"""
        if not self.camera or not self.camera.streaming:
            return Response("Error: Streaming not active", status=400, mimetype='text/plain')
        
        with self.camera.frame_lock:
            if self.camera.latest_frame:
                response = Response(
                    self.camera.latest_frame,
                    mimetype='image/jpeg',
                    headers={
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                        'Expires': '0',
                        'Access-Control-Allow-Origin': '*'
                    }
                )
                return response
        
        return Response("Error: No frame available", status=503, mimetype='text/plain')
    
    def handle_detection_alert(self, alert_type):
        """Handle object detection alerts"""
        current_time = time.time() * 1000
        
        if alert_type == "suspicious_activity":
            # Check cooldown to prevent spam
            if (current_time - self.last_notification_time) > NOTIFICATION_COOLDOWN:
                # Set alert data
                self.current_data.alert = True
                self.current_data.alertType = "suspicious_activity"
                self.last_alert_time = current_time
                self.last_notification_time = current_time
                
                # Trigger hardware alerts (LED red + buzzer)
                self.last_hardware_trigger_time = current_time
                
                print(f"🚨 SUSPICIOUS ACTIVITY DETECTED!")
                print(f"🔴 Camera stream will flash red for 2 seconds")
                print(f"🚨 Notification sent (cooldown: {NOTIFICATION_COOLDOWN/1000}s)")
            else:
                print(f"🔇 Suspicious activity detected but notification suppressed (cooldown active)")
    
    def enable_object_detection(self) -> dict:
        """Enable object detection"""
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        if self.camera.enable_detection():
            return {"success": True, "message": "Object detection enabled"}
        else:
            return {"error": "Failed to enable object detection"}
    
    def disable_object_detection(self) -> dict:
        """Disable object detection"""
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        self.camera.disable_detection()
        return {"success": True, "message": "Object detection disabled"}
    
    def get_detection_status(self) -> dict:
        """Get object detection status"""
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        camera_status = self.camera.get_camera_status()
        return {
            "detection_enabled": camera_status.get('detection_enabled', False),
            "detector_status": camera_status.get('detector_status', None),
            "camera_streaming": camera_status.get('streaming', False)
        }
    
    def set_detection_model(self, model_name) -> dict:
        """Set detection model"""
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        if self.camera.set_detection_model(model_name):
            return {"success": True, "message": f"Detection model set to {model_name}"}
        else:
            return {"error": f"Failed to set detection model to {model_name}"}
    
    def read_imu_data(self):
        """Read IMU data - exact Arduino equivalent"""
        try:
            # Arduino: Wire.beginTransmission + Wire.write + Wire.endTransmission(false)
            # Arduino: Wire.requestFrom(MPU6050_ADDR, 14, true)
            
            # Read 14 bytes starting from accelerometer register
            data = self.bus.read_i2c_block_data(MPU6050_ADDR, MPU6050_ACCEL_XOUT_H, 14)
            
            if len(data) >= 14:
                # Arduino: int16_t ax_raw = Wire.read() << 8 | Wire.read()
                ax_raw = (data[0] << 8) | data[1]
                ay_raw = (data[2] << 8) | data[3]
                az_raw = (data[4] << 8) | data[5]
                
                temp_raw = (data[6] << 8) | data[7]
                
                gx_raw = (data[8] << 8) | data[9]
                gy_raw = (data[10] << 8) | data[11]
                gz_raw = (data[12] << 8) | data[13]
                
                # Convert to signed 16-bit
                def to_signed_16(val):
                    return val if val < 32768 else val - 65536
                
                ax_raw = to_signed_16(ax_raw)
                ay_raw = to_signed_16(ay_raw)
                az_raw = to_signed_16(az_raw)
                temp_raw = to_signed_16(temp_raw)
                gx_raw = to_signed_16(gx_raw)
                gy_raw = to_signed_16(gy_raw)
                gz_raw = to_signed_16(gz_raw)
                
                # Arduino: currentData.ax = ax_raw / 16384.0
                self.current_data.ax = ax_raw / 16384.0
                self.current_data.ay = ay_raw / 16384.0
                self.current_data.az = az_raw / 16384.0
                self.current_data.temp = temp_raw / 340.0 + 36.53
                self.current_data.gx = gx_raw / 131.0
                self.current_data.gy = gy_raw / 131.0
                self.current_data.gz = gz_raw / 131.0
                
                # Arduino debug print equivalent
                current_time = time.time() * 1000
                if hasattr(self, 'last_debug_time'):
                    if current_time - self.last_debug_time > 5000:  # 5 seconds
                        print(f"Raw IMU - Accel: {ax_raw}, {ay_raw}, {az_raw} | "
                              f"Gyro: {gx_raw}, {gy_raw}, {gz_raw} | Temp: {temp_raw}")
                        self.last_debug_time = current_time
                else:
                    self.last_debug_time = current_time
            else:
                print("Warning: Not enough data from MPU6050")
                
        except Exception as e:
            print(f"Error reading IMU data: {e}")
    
    def detect_events(self):
        """Detect events - exact Arduino equivalent"""
        # Arduino: float accel_magnitude = sqrt(...)
        accel_magnitude = math.sqrt(
            self.current_data.ax * self.current_data.ax +
            self.current_data.ay * self.current_data.ay +
            self.current_data.az * self.current_data.az
        )
        
        gyro_magnitude = math.sqrt(
            self.current_data.gx * self.current_data.gx +
            self.current_data.gy * self.current_data.gy +
            self.current_data.gz * self.current_data.gz
        )
        
        current_time = time.time() * 1000  # milliseconds like Arduino
        
        # Check if enough time has passed since last notification (prevent spam)
        can_send_notification = (current_time - self.last_notification_time) > NOTIFICATION_COOLDOWN
        
        # Arduino fall detection logic
        if accel_magnitude > FALL_THRESHOLD and not self.fall_detected:
            self.fall_detected = True
            print("FALL DETECTED!")
            if can_send_notification:
                self.current_data.alert = True
                self.current_data.alertType = "fall"
                self.last_alert_time = current_time  # Set alert start time
                self.last_notification_time = current_time
                print(f"🚨 Fall notification sent (cooldown: {NOTIFICATION_COOLDOWN/1000}s)")
            else:
                print(f"🔇 Fall detected but notification suppressed (cooldown active)")
        elif accel_magnitude <= FALL_THRESHOLD:
            self.fall_detected = False
        
        # Arduino movement detection logic  
        if gyro_magnitude > MOVEMENT_THRESHOLD and not self.movement_detected:
            self.movement_detected = True
            print("UNUSUAL MOVEMENT DETECTED!")
            if can_send_notification:
                self.current_data.alert = True
                self.current_data.alertType = "movement"
                self.last_alert_time = current_time  # Set alert start time
                self.last_notification_time = current_time
                print(f"🚨 Movement notification sent (cooldown: {NOTIFICATION_COOLDOWN/1000}s)")
            else:
                print(f"🔇 Movement detected but notification suppressed (cooldown active)")
        elif gyro_magnitude <= MOVEMENT_THRESHOLD:
            self.movement_detected = False
        
        # LED and BUZZER control - stay active for 2 seconds after detection
        should_trigger_hardware = self.fall_detected or self.movement_detected
        
        # If movement/fall is detected, update the trigger time
        if should_trigger_hardware:
            self.last_hardware_trigger_time = current_time
        
        # Keep LED red and buzzer active for 2 seconds after last detection
        hardware_timeout = 2000  # 2 seconds
        time_since_trigger = current_time - self.last_hardware_trigger_time
        hardware_should_be_active = time_since_trigger < hardware_timeout
        
        if hardware_should_be_active:
            if self.led:
                self.led.red()  # LED red for 2 seconds after movement/fall
            if self.buzzer and not self.buzzer.is_active:
                self.buzzer.start_tone()  # Start buzzer for 2 seconds after movement/fall
                print("🔊 BUZZER ON - Movement/Fall detected (2s duration)")
        else:
            if self.led:
                self.led.green()  # LED green when 2s timeout expires
            if self.buzzer and self.buzzer.is_active:
                self.buzzer.stop_tone()  # Stop buzzer when 2s timeout expires
                print("🔇 BUZZER OFF - 2s timeout expired")
        
        # Arduino alert timeout logic - clear notification alert after 2 seconds
        if self.current_data.alert and current_time - self.last_alert_time > 2000:
            self.current_data.alert = False
            self.current_data.alertType = ""
            print(f"🔄 Alert notification reset after 2s timeout")
        
        # Arduino debug print equivalent (every 1 second)
        if hasattr(self, 'last_print_time'):
            if current_time - self.last_print_time > 1000:  # 1 second
                cooldown_remaining = max(0, NOTIFICATION_COOLDOWN - (current_time - self.last_notification_time))
                alert_status = f"{self.current_data.alertType}" if self.current_data.alert else "None"
                print(f"Accel: {self.current_data.ax:.2f}, {self.current_data.ay:.2f}, {self.current_data.az:.2f} | "
                      f"Gyro: {self.current_data.gx:.2f}, {self.current_data.gy:.2f}, {self.current_data.gz:.2f} | "
                      f"Temp: {self.current_data.temp:.1f}°C | Alert: {alert_status} | "
                      f"Cooldown: {cooldown_remaining/1000:.1f}s")
                self.last_print_time = current_time
        else:
            self.last_print_time = current_time
    
    def trigger_loud_buzzer(self):
        """Trigger loud buzzer for alerts - 100% duty cycle"""
        if self.buzzer:
            # Use threading to avoid blocking the main loop
            import threading
            buzz_thread = threading.Thread(
                target=self.buzzer.beep, 
                args=(ALERT_DURATION,),
                daemon=True
            )
            buzz_thread.start()
            print(f"🔊 100% DUTY CYCLE BUZZER ACTIVATED at {BUZZER_FREQUENCY}Hz")
    
    def stop_buzzer(self):
        """Stop buzzer"""
        if self.buzzer:
            self.buzzer.stop_tone()
            print("🔇 Buzzer stopped")
    
    def main_loop(self):
        """Main loop - exact Arduino loop() equivalent"""
        while self.running:
            current_time = time.time() * 1000  # milliseconds like Arduino
            
            # Arduino: if (millis() - lastDataTime >= DATA_INTERVAL)
            if current_time - self.last_data_time >= DATA_INTERVAL:
                self.read_imu_data()
                self.detect_events()
                self.last_data_time = current_time
            
            time.sleep(0.01)  # Small delay to prevent excessive CPU usage
    
    def run_server(self):
        """Run the Flask server"""
        try:
            local_ip = self.get_local_ip()
            print(f"🌐 GuardIt IMU Server starting...")
            print(f"📡 Local IP: {local_ip}")
            print(f"🔌 Port: {SERVER_PORT}")
            print(f"🔗 Full URL: http://{local_ip}:{SERVER_PORT}")
            print(f"📱 Configure iOS app to connect to: {local_ip}:{SERVER_PORT}")
            print(f"✅ Server ready - waiting for iOS app connection...")
            self.app.run(host='0.0.0.0', port=SERVER_PORT, debug=False)
        except KeyboardInterrupt:
            print("\nServer stopped by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        
        # Stop camera streaming
        if self.camera:
            if self.camera.streaming:
                self.camera.stop_streaming()
            if self.camera.csi_streaming:
                self.camera.stop_csi_streaming()
            self.camera.cleanup()
        
        # Clean up hardware
        if self.buzzer:
            self.buzzer.cleanup()
        if self.led:
            self.led.cleanup()
        
        GPIO.cleanup()
        print("🧹 All resources cleaned up")
        print("Cleanup completed")

def main():
    """Main function - Arduino setup() + loop() equivalent"""
    try:
        # Clean up any previous GPIO state before starting
        try:
            GPIO.cleanup()
        except Exception:
            pass  # Ignore cleanup errors if GPIO wasn't previously used
        
        server = GuardItIMUServer()
        server.run_server()
    except KeyboardInterrupt:
        print("\nServer stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up streaming and GPIO on exit
        try:
            # Stop camera streaming if running
            if 'server' in locals() and hasattr(server, 'camera') and server.camera:
                if server.camera.streaming:
                    server.camera.stop_streaming()
                if server.camera.csi_streaming:
                    server.camera.stop_csi_streaming()
            
            GPIO.cleanup()
            print("🧹 Cleanup completed - GPIO and camera streaming stopped")
        except Exception as cleanup_error:
            print(f"Cleanup error (ignored): {cleanup_error}")

if __name__ == "__main__":
    main()

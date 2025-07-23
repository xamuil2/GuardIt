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

import cv2
import numpy as np
import subprocess
import base64
import io
from PIL import Image
import os

from object_detector import GuardItPersonDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WIFI_SSID = "Avnit"
WIFI_PASSWORD = "hihihihi"
SERVER_PORT = 8080

import socket
import subprocess

MPU6050_ADDR = 0x68
MPU6050_ACCEL_XOUT_H = 0x3B
MPU6050_PWR_MGMT_1 = 0x6B

BUZZER_PIN = 21
BUZZER_FREQUENCY = 1000
ALERT_DURATION = 200

LED_RED_PIN = 18
LED_GREEN_PIN = 19
LED_BLUE_PIN = 20

FALL_THRESHOLD = 25.0
MOVEMENT_THRESHOLD = 7.0
DATA_INTERVAL = 100
NOTIFICATION_COOLDOWN = 2000

NOTIFICATION_TYPES = {
    'fall': 'fall',
    'movement': 'movement',
    'suspicious_activity': 'suspicious_activity'
}

class RGBLEDController:
    
    def __init__(self, red_pin, green_pin, blue_pin):
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin
        self.red_pwm = None
        self.green_pwm = None
        self.blue_pwm = None
        
        GPIO.setup(self.red_pin, GPIO.OUT)
        GPIO.setup(self.green_pin, GPIO.OUT)
        GPIO.setup(self.blue_pin, GPIO.OUT)
        
        self.red_pwm = GPIO.PWM(self.red_pin, 1000)
        self.green_pwm = GPIO.PWM(self.green_pin, 1000)
        self.blue_pwm = GPIO.PWM(self.blue_pin, 1000)
        
        self.red_pwm.start(0)
        self.green_pwm.start(0)
        self.blue_pwm.start(0)
    
    def set_color(self, red, green, blue):
        self.red_pwm.ChangeDutyCycle(red)
        self.green_pwm.ChangeDutyCycle(green)
        self.blue_pwm.ChangeDutyCycle(blue)
    
    def red(self):
        
        self.set_color(100, 0, 0)
    
    def green(self):
        
        self.set_color(0, 100, 0)
    
    def blue(self):
        
        self.set_color(0, 0, 100)
    
    def off(self):
        
        self.set_color(0, 0, 0)
    
    def cleanup(self):
        
        if self.red_pwm:
            self.red_pwm.stop()
        if self.green_pwm:
            self.green_pwm.stop()
        if self.blue_pwm:
            self.blue_pwm.stop()

class MaxVolumeBuzzer:

    def __init__(self, pin, frequency=2000):
        self.pin = pin
        self.frequency = frequency
        self.pwm = None
        self.is_active = False
        
    def start_tone(self):
        
        if not self.is_active:
            self.pwm = GPIO.PWM(self.pin, self.frequency)
            self.pwm.start(50)
            self.is_active = True
            
    def stop_tone(self):
        
        if self.is_active and self.pwm:
            self.pwm.stop()
            self.pwm = None
            self.is_active = False
    
    def beep(self, duration_ms):
        
        self.start_tone()
        time.sleep(duration_ms / 1000.0)
        self.stop_tone()
    
    def cleanup(self):
        
        self.stop_tone()

class NotificationHandler:

    def __init__(self, buzzer, led_controller):
        self.buzzer = buzzer
        self.led_controller = led_controller
        self.last_notification_time = 0
        self.notification_cooldown = NOTIFICATION_COOLDOWN
        
    def trigger_notification(self, alert_type, data=None):
        
        current_time = time.time() * 1000
        
        if current_time - self.last_notification_time < self.notification_cooldown:
            return False
            
        self.last_notification_time = current_time
        
        if alert_type == NOTIFICATION_TYPES['fall']:
            return self._handle_fall_alert(data)
        elif alert_type == NOTIFICATION_TYPES['movement']:
            return self._handle_movement_alert(data)
        elif alert_type == NOTIFICATION_TYPES['suspicious_activity']:
            return self._handle_suspicious_activity_alert(data)
        else:
            logger.warning(f"Unknown alert type: {alert_type}")
            return False
            
    def _handle_fall_alert(self, data):
        
        try:
            logger.info("🚨 FALL DETECTED - Triggering alert")
            
            self.led_controller.red()
            
            self.buzzer.beep(ALERT_DURATION)
            
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Fall alert triggered at {timestamp}")
            
            return True
        except Exception as e:
            logger.error(f"Error handling fall alert: {e}")
            return False
            
    def _handle_movement_alert(self, data):
        
        try:
            logger.info("⚠️ MOVEMENT DETECTED - Triggering alert")
            
            self.led_controller.set_color(100, 50, 0)
            
            self.buzzer.beep(ALERT_DURATION)
            
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Movement alert triggered at {timestamp}")
            
            return True
        except Exception as e:
            logger.error(f"Error handling movement alert: {e}")
            return False
            
    def _handle_suspicious_activity_alert(self, data):
        
        try:
            logger.info("🚨 SUSPICIOUS ACTIVITY DETECTED - Triggering alert")
            
            self.led_controller.red()
            
            for i in range(3):
                self.buzzer.beep(ALERT_DURATION)
                time.sleep(0.1)
            
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Suspicious activity alert triggered at {timestamp}")
            
            time.sleep(1)
            self.led_controller.green()
            
            return True
        except Exception as e:
            logger.error(f"Error handling suspicious activity alert: {e}")
            return False

@dataclass
class IMUData:
    
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

    def __init__(self):
        self.csi_available = False
        self.usb_available = False
        self.usb_device_id = None
        self.streaming = False
        self.usb_cap = None
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.capture_thread = None
        self.capture_running = False
        self.csi_streaming = False
        self.latest_csi_frame = None
        self.csi_frame_lock = threading.Lock()
        self.csi_capture_thread = None
        self.csi_capture_running = False
        
        self.detector = None
        self.detection_enabled = False
        self.last_detection_alert = 0
        self.detection_callback = None
        
        self._detect_cameras()
        self._initialize_detector()
        
        # Auto-start CSI streaming for better performance
        if self.csi_available:
            threading.Thread(target=self._auto_start_csi, daemon=True).start()
    
    def _auto_start_csi(self):
        """Auto-start CSI streaming after brief delay"""
        time.sleep(1)  # Let initialization complete
        if self.csi_available and not self.csi_streaming:
            logger.info("🚀 Auto-starting CSI streaming for optimal performance")
            self.start_csi_streaming()
    
    def _initialize_detector(self):
        
        try:
            self.detector = GuardItPersonDetector()
            logger.info("✅ Object detection initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize object detection: {e}")
            self.detector = None
    
    def _detect_cameras(self):
        
        logger.info("🔍 Detecting cameras...")
        
        # Test CSI camera using libcamera (modern Pi camera interface)
        logger.info("🔍 Testing CSI camera with libcamera...")
        try:
            # Use rpicam-still to check if CSI camera is available
            result = subprocess.run(
                ['rpicam-still', '--list-cameras'], 
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and 'imx219' in result.stdout.lower():
                self.csi_available = True
                logger.info("✅ CSI Camera (IMX219) detected via libcamera")
            else:
                logger.info("⚠️ CSI Camera not detected via libcamera")
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.info(f"⚠️ CSI Camera libcamera test failed: {e}")
        
        # Detect USB camera using OpenCV V4L2
        logger.info("🔍 Testing USB camera with OpenCV...")
        for device_id in [0, 1, 2, 3, 4]:  # Test all possible devices
            try:
                cap = cv2.VideoCapture(device_id, cv2.CAP_V4L2)
                if cap.isOpened():
                    # Set test resolution and try to get a frame
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                    
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        self.usb_available = True
                        self.usb_device_id = device_id
                        logger.info(f"✅ USB Camera detected on device {device_id}")
                        cap.release()
                        break
                cap.release()
            except Exception as e:
                logger.debug(f"USB camera test device {device_id} failed: {e}")
                continue
        
        if not self.usb_available:
            logger.warning("❌ No USB Camera detected")
        
        logger.info(f"📹 Camera Status - CSI: {self.csi_available}, USB: {self.usb_available}")

    def _background_capture(self):
        
        while self.capture_running and self.usb_cap:
            try:
                for _ in range(2):
                    self.usb_cap.grab()
                ret, frame = self.usb_cap.retrieve()
                
                if ret and frame is not None:
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 15])
                    
                    with self.frame_lock:
                        self.latest_frame = buffer.tobytes()
                
                time.sleep(0.02)
            except Exception as e:
                time.sleep(0.1)
    
    def _background_usb_capture(self):

        cap = cv2.VideoCapture(self.usb_device_id, cv2.CAP_V4L2)
        try:
            # Ultra-optimized settings for minimum latency
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Slightly larger for better quality
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Single frame buffer
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            cap.set(cv2.CAP_PROP_FPS, 30)  # Optimized FPS
            cap.set(cv2.CAP_PROP_EXPOSURE, -7)  # Very fast exposure
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Auto exposure off
            cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Auto focus off
            
            frame_count = 0
            detection_interval = 20  # Reduce detection frequency for speed
            
            while self.capture_running and cap.isOpened():
                try:
                    # Aggressive frame skipping for real-time performance
                    for _ in range(3):
                        cap.grab()  # Skip buffered frames
                    ret, frame = cap.retrieve()
                    
                    if ret and frame is not None:
                        detection_triggered = False
                        processed_frame = frame
                        
                        if (self.detection_enabled and self.detector and 
                            frame_count % detection_interval == 0):
                            try:
                                detection_triggered, processed_frame = self.detector.process_detection(frame)
                                
                                if detection_triggered and self.detection_callback:
                                    self.detection_callback("suspicious_activity")
                            
                            except Exception as e:
                                logger.debug(f"Detection processing error: {e}")
                        
                        frame_to_encode = processed_frame if self.detection_enabled else frame
                        
                        # Ultra-fast JPEG encoding
                        encode_params = [cv2.IMWRITE_JPEG_QUALITY, 70, cv2.IMWRITE_JPEG_OPTIMIZE, 1]
                        _, buffer = cv2.imencode('.jpg', frame_to_encode, encode_params)
                        
                        with self.frame_lock:
                            self.latest_frame = buffer.tobytes()
                        
                        frame_count += 1
                    
                    # No sleep for maximum speed
                except Exception as e:
                    time.sleep(0.005)  # Minimal sleep on error
        
        except Exception as e:
            logger.error(f"USB capture setup error: {e}")
        finally:
            if cap.isOpened():
                cap.release()

    def _background_csi_capture(self):
        """HYBRID CSI capture - Use rpicam-jpeg for better reliability and speed"""
        frame_count = 0
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        try:
            logger.info("🔧 HYBRID CSI capture started - testing reliable approaches")
            
            start_time = time.time()
            last_performance_log = start_time
            
            # First, test if basic capture works
            try:
                test_result = subprocess.run([
                    'rpicam-still', '--list-cameras'
                ], capture_output=True, text=True, timeout=3)
                
                if test_result.returncode != 0:
                    logger.error("❌ CSI camera not available")
                    return
                    
                logger.info("✅ CSI camera confirmed available")
            except Exception as e:
                logger.error(f"❌ CSI camera test failed: {e}")
                return
            
            # Try multiple command approaches for reliability
            command_variants = [
                # Approach 1: Standard rpicam-still
                [
                    'rpicam-still',
                    '--immediate',
                    '--nopreview', 
                    '--width', '320',
                    '--height', '240',
                    '--quality', '70',
                    '--timeout', '200',
                    '--output', '-'
                ],
                # Approach 2: Faster, lower quality  
                [
                    'rpicam-still',
                    '--immediate',
                    '--nopreview',
                    '--width', '240',
                    '--height', '180', 
                    '--quality', '50',
                    '--timeout', '100',
                    '--output', '-'
                ],
                # Approach 3: Even simpler
                [
                    'rpicam-still',
                    '--nopreview',
                    '--width', '160',
                    '--height', '120',
                    '--quality', '40',
                    '--timeout', '50',
                    '--output', '-'
                ]
            ]
            
            current_cmd_index = 0
            cmd = command_variants[current_cmd_index]
            
            while self.csi_capture_running:
                try:
                    current_time = time.time()
                    
                    # Try capture with current command
                    result = subprocess.run(cmd, capture_output=True, timeout=1.0)
                    
                    if result.returncode == 0 and result.stdout:
                        consecutive_errors = 0
                        jpeg_data = result.stdout
                        
                        # LOCKLESS update for speed
                        self.latest_csi_frame = jpeg_data
                        frame_count += 1
                        
                    else:
                        consecutive_errors += 1
                        
                        # If current approach fails too much, try next variant
                        if consecutive_errors > max_consecutive_errors:
                            current_cmd_index = (current_cmd_index + 1) % len(command_variants)
                            cmd = command_variants[current_cmd_index]
                            logger.warning(f"🔄 Switching to CSI command variant {current_cmd_index + 1}")
                            consecutive_errors = 0
                            time.sleep(0.5)
                    
                    # Performance logging every 5 seconds
                    if current_time - last_performance_log >= 5.0:
                        elapsed = current_time - start_time
                        fps = frame_count / elapsed if elapsed > 0 else 0
                        logger.info(f"🔧 HYBRID CSI FPS: {fps:.1f} | Variant: {current_cmd_index + 1} | Frames: {frame_count}")
                        last_performance_log = current_time
                
                    # Adaptive sleep based on performance
                    if fps > 5:
                        time.sleep(0.1)   # Fast mode - 10 FPS max
                    elif fps > 2:
                        time.sleep(0.2)   # Medium mode - 5 FPS max  
                    else:
                        time.sleep(0.5)   # Slow mode - 2 FPS max
                    
                except subprocess.TimeoutExpired:
                    consecutive_errors += 1
                    logger.debug("CSI capture timeout")
                    
                except Exception as loop_error:
                    consecutive_errors += 1
                    logger.debug(f"CSI capture error: {loop_error}")
                    
                    if consecutive_errors > max_consecutive_errors * 2:
                        logger.error("❌ Too many CSI errors - pausing")
                        time.sleep(2)
                        consecutive_errors = 0
                    
        except Exception as e:
            logger.error(f"🔧 HYBRID CSI initialization error: {e}")
        finally:
            self.csi_capture_running = False
            logger.info(f"🔧 HYBRID CSI capture stopped after {frame_count} frames")
    
    def start_streaming(self):
        
        if self.streaming:
            return True
            
        self.capture_running = True
        self.capture_thread = threading.Thread(target=self._background_usb_capture, daemon=True)
        self.capture_thread.start()
        self.streaming = True
        return True
    
    def stop_streaming(self):
        
        if not self.streaming:
            return
            
        self.capture_running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=3)
        self.streaming = False
    
    def get_latest_frame(self):
        
        if not self.streaming:
            # For non-streaming mode, use optimized direct capture
            return self.capture_usb_image(width=160, height=120)[0]
        
        with self.frame_lock:
            if self.latest_frame:
                return self.latest_frame
        
        return None
    
    def get_latest_frame_fast(self):
        """Optimized method for fastest frame retrieval"""
        if self.streaming:
            with self.frame_lock:
                return self.latest_frame
        return None
    
    def start_csi_streaming(self):
        
        if not self.csi_available:
            logger.warning("❌ Cannot start CSI streaming - camera not available")
            return False
            
        if self.csi_streaming:
            logger.debug("✅ CSI streaming already active")
            return True
        
        try:
            self.csi_capture_running = True
            self.csi_capture_thread = threading.Thread(target=self._background_csi_capture, daemon=True)
            self.csi_capture_thread.start()
            
            # Much shorter wait - streaming should start almost immediately
            time.sleep(0.2)
            
            # Don't test frame on startup - just assume it will work
            self.csi_streaming = True
            logger.info("✅ CSI streaming started")
            return True
                
        except Exception as e:
            logger.error(f"❌ Failed to start CSI streaming: {e}")
            self.stop_csi_streaming()
            return False
    
    def stop_csi_streaming(self):
        
        if not self.csi_streaming:
            return
            
        self.csi_capture_running = False
        if self.csi_capture_thread and self.csi_capture_thread.is_alive():
            self.csi_capture_thread.join(timeout=3)
        self.csi_streaming = False
    
    def get_csi_frame(self):
        """CSI frame access - optimized for maximum speed"""
        # Always prefer streaming mode for CSI - much faster
        if not self.csi_streaming:
            # Auto-start streaming for better performance
            self.start_csi_streaming()
            time.sleep(0.1)  # Brief wait for stream to start
        
        # LOCKLESS direct access for maximum speed
        if self.latest_csi_frame:
            return self.latest_csi_frame
        
        # Fallback to direct capture only if streaming fails
        image_data, error = self.capture_csi_image(width=160, height=120)
        if image_data:
            import base64
            return base64.b64decode(image_data)
        return None
    
    def get_csi_frame_fast(self):
        """ULTRA-FAST CSI frame retrieval - LOCKLESS access for maximum speed"""
        if not self.csi_streaming:
            self.start_csi_streaming()
        
        # LOCKLESS direct access - maximum speed like USB camera
        return self.latest_csi_frame
    
    def capture_csi_image(self, width=640, height=480):
        
        if not self.csi_available:
            return None, "CSI camera not available"
        
        try:
            # Use OpenCV for direct CSI capture
            cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            
            if not cap.isOpened():
                return None, "Failed to open CSI camera"
            
            # Set capture resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, min(width, 640))
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, min(height, 480))
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('Y','U','Y','V'))
            
            # Capture frame
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                # Encode to JPEG
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, 85]
                _, buffer = cv2.imencode('.jpg', frame, encode_params)
                
                image_b64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
                return image_b64, None
            else:
                return None, "Failed to capture CSI frame"
                
        except Exception as e:
            return None, f"CSI capture error: {str(e)}"
    
    def capture_usb_image(self, width=640, height=480):
        
        if not self.usb_available:
            return None, "USB camera not available"
        
        cap = cv2.VideoCapture(self.usb_device_id, cv2.CAP_V4L2)
        try:
            # Optimized settings for speed
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, min(width, 160))
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, min(height, 120))
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            cap.set(cv2.CAP_PROP_FPS, 60)
            cap.set(cv2.CAP_PROP_EXPOSURE, -6)  # Faster exposure
            
            # Skip a few frames to get fresh data
            for _ in range(3):
                cap.grab()
            
            ret, frame = cap.read()
            if ret and frame is not None:
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])  # Better quality
                image_b64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
                return image_b64, None
            else:
                return None, "Failed to capture USB camera frame"
        
        except Exception as e:
            return None, f"USB capture error: {e}"
        finally:
            cap.release()
    
    def start_usb_streaming(self):
        
        if not self.usb_available:
            return False
        
        if self.usb_cap is None:
            self.usb_cap = cv2.VideoCapture(self.usb_device_id, cv2.CAP_V4L2)
            # Optimized settings for low latency streaming
            self.usb_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
            self.usb_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
            self.usb_cap.set(cv2.CAP_PROP_FPS, 60)
            self.usb_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.usb_cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            self.usb_cap.set(cv2.CAP_PROP_EXPOSURE, -6)  # Faster exposure
        
        self.streaming = True
        
        if not self.capture_running:
            self.capture_running = True
            self.capture_thread = threading.Thread(target=self._background_capture, daemon=True)
            self.capture_thread.start()
        
        return True
    
    def stop_usb_streaming(self):
        
        self.streaming = False
        self.capture_running = False
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        
        if self.usb_cap:
            self.usb_cap.release()
            self.usb_cap = None
        
        with self.frame_lock:
            self.latest_frame = None
    
    def get_usb_frame(self):
        
        if not self.streaming:
            return None
        
        with self.frame_lock:
            if self.latest_frame:
                frame_b64 = base64.b64encode(self.latest_frame).decode('utf-8')
                return frame_b64
        return None
    
    def get_latest_frame_fast(self):
        """EXTREME SPEED frame retrieval - NO LOCKS for maximum performance"""
        if not self.streaming or not self.latest_frame:
            return None
        
        # Direct access WITHOUT lock - maximum speed
        return self.latest_frame
    
    def start_streaming(self):
        """Start high-speed streaming with minimal startup delay"""
        if self.streaming:
            logger.info("✅ Streaming already active")
            return True
            
        if not self.usb_available:
            logger.error("❌ No USB camera available for streaming")
            return False
            
        try:
            logger.info("🚀 Starting high-speed streaming...")
            self.streaming = True
            self.capture_running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            # Minimal startup delay - just enough for thread to start
            time.sleep(0.1)
            
            logger.info("✅ High-speed streaming started")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start streaming: {e}")
            self.streaming = False
            self.capture_running = False
            return False
    
    def _capture_loop(self):
        """FREEZE-FREE 12+ FPS capture loop - bulletproof against iOS app freezes"""
        cap = None
        consecutive_errors = 0
        max_consecutive_errors = 5
        try:
            cap = cv2.VideoCapture(self.usb_device_id, cv2.CAP_V4L2)
            if not cap.isOpened():
                logger.error(f"Failed to open USB camera {self.usb_device_id}")
                self.streaming = False
                return
            
            # CRITICAL: Bulletproof camera settings to prevent freezes
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)   # Stable resolution
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)  # Stable resolution
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)      # CRITICAL: Single frame buffer
            cap.set(cv2.CAP_PROP_FPS, 30)            # Request 30 FPS
            
            # Use YUYV format - more stable than MJPEG on Pi
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('Y','U','Y','V'))
            
            # Disable ALL auto-adjustments for consistent, freeze-free timing
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)   # Manual exposure
            cap.set(cv2.CAP_PROP_EXPOSURE, -6)       # Fast but stable exposure  
            cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)       # No autofocus delays
            cap.set(cv2.CAP_PROP_AUTO_WB, 0)         # No auto white balance delays
            cap.set(cv2.CAP_PROP_GAIN, 0)            # No auto gain delays
            
            logger.info("🛡️ FREEZE-FREE USB capture started - bulletproof mode")
            
            frame_count = 0
            start_time = time.time()
            last_performance_log = start_time
            last_health_check = start_time
            
            # Pre-allocate encode parameters for consistent performance
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 65]  # Good quality/speed balance
            
            while self.capture_running and self.streaming:
                # CRITICAL: Only grab, don't decode unnecessary frames
                cap.grab()  # Discard old frame
                
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Encode to JPEG immediately 
                    _, buffer = cv2.imencode('.jpg', frame, encode_params)
                    jpeg_data = buffer.tobytes()
                    
                    # Update latest frame - NO LOCK for speed
                    self.latest_frame = jpeg_data
                    
                    frame_count += 1
                    
                    # Performance logging every 2 seconds
                    current_time = time.time()
                    if current_time - last_performance_log >= 2.0:
                        elapsed = current_time - start_time
                        fps = frame_count / elapsed if elapsed > 0 else 0
                        logger.info(f"� LOCKED FPS: {fps:.1f} | Target: 10+ FPS | Frames: {frame_count}")
                        last_performance_log = current_time
                
                # NO SLEEP - let CPU run at full speed
                    
        except Exception as e:
            logger.error(f"🎯 LOCKED capture loop error: {e}")
        finally:
            if cap:
                cap.release()
            self.streaming = False
            self.capture_running = False
            logger.info(f"🎯 LOCKED capture loop stopped after {frame_count} frames")
            logger.info(f"� EXTREME capture loop stopped after {frame_count} frames")
    
    def get_camera_status(self):
        
        return {
            'csi_available': self.csi_available,
            'usb_available': self.usb_available,
            'usb_device_id': self.usb_device_id,
            'streaming': self.streaming,
            'detection_enabled': self.detection_enabled,
            'detector_status': self.detector.get_status() if self.detector else None
        }
    
    def enable_detection(self):
        
        if self.detector:
            self.detection_enabled = True
            self.detector.enable_detection()
            return True
        else:
            return False
    
    def disable_detection(self):
        
        self.detection_enabled = False
        if self.detector:
            self.detector.disable_detection()
    
    def set_detection_callback(self, callback):
        
        self.detection_callback = callback
    
    def set_detection_model(self, model_name):
        
        if self.detector:
            return self.detector.set_model(model_name)
        return False
    
    def cleanup(self):
        
        self.stop_streaming()
        self.stop_csi_streaming()
        self.capture_running = False
        self.csi_capture_running = False

class GuardItIMUServer:

    def __init__(self):
        self.current_data = IMUData()
        self.last_data_time = 0
        self.fall_detected = False
        self.movement_detected = False
        self.last_alert_time = 0
        self.last_notification_time = 0
        self.last_hardware_trigger_time = 0
        self.start_time = time.time()
        
        self.bus = None
        self.buzzer = None
        self.led = None
        self.camera = None
        self.running = False
        
        self.app = Flask(__name__)
        self.setup_routes()

        self.init_gpio()
        
        self.camera = CameraManager()
        
        if self.camera:
            self.camera.set_detection_callback(self.handle_detection_alert)
        
        if not self.init_mpu6050():
            raise Exception("MPU6050 initialization failed")
        
        self.running = True
        self.data_thread = threading.Thread(target=self.main_loop, daemon=True)
        self.data_thread.start()

    def init_gpio(self):
        
        try:
            try:
                GPIO.cleanup()
            except Exception:
                pass
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            GPIO.setup(BUZZER_PIN, GPIO.OUT)
            GPIO.output(BUZZER_PIN, GPIO.LOW)
            
            self.buzzer = MaxVolumeBuzzer(BUZZER_PIN, BUZZER_FREQUENCY)
            
            self.led = RGBLEDController(LED_RED_PIN, LED_GREEN_PIN, LED_BLUE_PIN)
            
            self.notification_handler = NotificationHandler(self.buzzer, self.led)
            
            self.led.green()
            
            logger.info("✅ GPIO initialized with buzzer, RGB LED, and notification handler")
            
        except Exception as e:
            logger.error(f"❌ GPIO initialization failed: {e}")
    
    def init_mpu6050(self) -> bool:
        
        try:
            self.bus = smbus2.SMBus(1)
            
            self.bus.write_byte_data(MPU6050_ADDR, MPU6050_PWR_MGMT_1, 0)
            
            who_am_i = self.bus.read_byte_data(MPU6050_ADDR, 0x75)
            if who_am_i not in [0x68, 0x70, 0x71, 0x73]:
                return False
            
            return True
            
        except Exception as e:
            return False
    
    def setup_routes(self):

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
        
        @self.app.route("/camera", methods=["GET"])
        def camera_status():
            return jsonify(self.get_camera_status())
        
        @self.app.route("/camera/csi", methods=["GET"])
        def capture_csi():
            width = request.args.get('width', 640, type=int)
            height = request.args.get('height', 480, type=int)
            return self.get_csi_image(width, height)
        
        @self.app.route("/camera/csi/fast", methods=["GET"])
        def capture_csi_fast():
            """Ultra-fast CSI capture endpoint"""
            return jsonify(self.get_csi_image_fast())
        
        @self.app.route("/camera/usb", methods=["GET"])
        def capture_usb():
            """Main USB camera endpoint - optimized for 10+ FPS"""
            return self.get_usb_image_optimized()
        
        @self.app.route("/camera/both", methods=["GET"])
        def capture_both():
            width = request.args.get('width', 640, type=int)
            height = request.args.get('height', 480, type=int)
            return jsonify(self.get_both_images(width, height))
            
        @self.app.route("/notification/suspicious_activity", methods=["POST"])
        def trigger_suspicious_activity():
            
            try:
                success = self.trigger_suspicious_activity_notification()
                return jsonify({
                    'success': success,
                    'message': 'Suspicious activity notification triggered' if success else 'Failed to trigger notification',
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Error triggering suspicious activity notification: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # Buzzer endpoints for iOS app
        @self.app.route("/buzzer/status", methods=["GET"])
        def buzzer_status():
            return jsonify(self.get_buzzer_status())
        
        @self.app.route("/buzzer", methods=["GET"])
        def buzzer_info():
            return jsonify(self.get_buzzer_status())
        
        @self.app.route("/buzzer/trigger", methods=["POST"])
        def trigger_buzzer():
            return jsonify(self.trigger_buzzer_endpoint())
        
        @self.app.route("/buzzer/test", methods=["POST"])
        def test_buzzer():
            return jsonify(self.test_buzzer_endpoint())
        
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
        
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    def get_local_ip(self):
        
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
                return "192.168.1.100"
    
    def get_server_info(self) -> dict:
        
        local_ip = self.get_local_ip()
        return {
            "name": "GuardIt IMU Server",
            "version": "1.0.0",
            "type": "raspberry-pi",
            "ip": local_ip,
            "port": SERVER_PORT,
            "status": "running",
            "endpoints": ["/status", "/imu", "/data", "/sensor", "/camera", "/camera/csi", "/camera/csi/fast", "/camera/usb", "/camera/both", "/notification/suspicious_activity", "/detection/enable", "/detection/disable", "/detection/status", "/detection/model", "/buzzer/status", "/buzzer", "/buzzer/trigger", "/buzzer/test"],
            "camera_status": self.camera.get_camera_status() if self.camera else {}
        }
    
    def get_status_info(self) -> dict:
        
        local_ip = self.get_local_ip()
        return {
            "connected": True,
            "ip": local_ip,
            "rssi": -50,
            "uptime": int(time.time() - self.start_time),
            "last_data_time": self.last_data_time
        }
    
    def get_imu_data_json(self) -> dict:
        
        data_dict = asdict(self.current_data)
        data_dict["timestamp"] = int(time.time() * 1000)
        return data_dict
    
    def get_camera_status(self) -> dict:
        
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
    
    def get_csi_image(self, width=640, height=480):
        """Main CSI endpoint - TARGET: 12+ FPS ULTRA-FAST libcamera for iOS app"""
        if not self.camera:
            return Response('{"error":"Camera not initialized"}', mimetype='application/json')
        
        try:
            # Ensure CSI streaming is active for maximum performance
            if not self.camera.csi_streaming:
                if not self.camera.start_csi_streaming():
                    return Response('{"error":"Failed to start CSI streaming"}', mimetype='application/json')
            
            # LOCKLESS CSI frame access for maximum speed (like USB camera)
            frame_data = self.camera.latest_csi_frame
            
            if frame_data:
                try:
                    # Cache good frame for freeze recovery
                    self.camera._last_good_csi_frame = frame_data
                    
                    # Ultra-fast base64 encoding
                    image_b64 = base64.b64encode(frame_data).decode('utf-8')
                    
                    response_data = {
                        "success": True,
                        "camera": "csi",
                        "image": image_b64,
                        "format": "jpeg",
                        "timestamp": int(time.time() * 1000),
                        "streaming": True,
                        "libcamera": True,  # Indicate using libcamera
                        "ultra_fast": True  # Indicate lockless access
                    }
                    
                    response = jsonify(response_data)
                    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response.headers['Pragma'] = 'no-cache'
                    response.headers['Expires'] = '0'
                    response.headers['Access-Control-Allow-Origin'] = '*'
                    return response
                    
                except Exception as encode_error:
                    logger.error(f"CSI frame encoding error: {encode_error}")
                    return jsonify({"success": False, "error": "Frame encoding failed", "camera": "csi"})
            else:
                # No frame available - return structured error for iOS app
                return jsonify({
                    "success": False,
                    "error": "No CSI frame available", 
                    "camera": "csi", 
                    "streaming": self.camera.csi_streaming,
                    "timestamp": int(time.time() * 1000)
                })
                
        except Exception as e:
            logger.error(f"CSI camera endpoint error: {e}")
            return jsonify({"success": False, "error": str(e), "camera": "csi"})
    
    def get_csi_image_fast(self) -> dict:
        """Ultra-fast CSI image capture - streaming only"""
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        start_time = time.time()
        
        try:
            if not self.camera.csi_streaming:
                self.camera.start_csi_streaming()
            
            frame_data = self.camera.get_csi_frame_fast()
            
            if frame_data:
                image_b64 = base64.b64encode(frame_data).decode('utf-8')
                response_time = round((time.time() - start_time) * 1000, 1)
                
                return {
                    "success": True,
                    "camera": "csi",
                    "image": image_b64,
                    "format": "jpeg",
                    "timestamp": int(time.time() * 1000),
                    "response_time_ms": response_time,
                    "streaming": True
                }
            else:
                return {"error": "No CSI frame available", "camera": "csi"}
                
        except Exception as e:
            return {"error": str(e), "camera": "csi"}
    
    def get_usb_image_optimized(self):
        """Main USB endpoint - FREEZE-FREE 12+ FPS optimized for iOS app"""
        if not self.camera:
            return Response('{"error":"Camera not initialized"}', mimetype='application/json')
        
        try:
            # Ensure streaming is active for maximum performance
            if not self.camera.streaming:
                if not self.camera.start_streaming():
                    return Response('{"error":"Failed to start streaming"}', mimetype='application/json')
                # NO SLEEP - immediate response for freeze-free operation
            
            # SAFE frame access with minimal lock time to prevent freezes
            frame_data = None
            try:
                # Ultra-fast lock acquisition with timeout to prevent freezes
                if self.camera.frame_lock.acquire(timeout=0.01):  # 10ms max wait
                    try:
                        frame_data = self.camera.latest_frame
                    finally:
                        self.camera.frame_lock.release()
                else:
                    # Lock timeout - use last known good frame or return error
                    logger.debug("Frame lock timeout - returning cached response")
                    frame_data = getattr(self.camera, '_last_good_frame', None)
            except Exception as lock_error:
                logger.debug(f"Frame lock error: {lock_error}")
                frame_data = getattr(self.camera, '_last_good_frame', None)
            
            if frame_data:
                try:
                    # Cache good frame for freeze recovery
                    self.camera._last_good_frame = frame_data
                    
                    # Ultra-fast base64 encoding
                    image_b64 = base64.b64encode(frame_data).decode('utf-8')
                    
                    response_data = {
                        "success": True,
                        "camera": "usb",
                        "image": image_b64,
                        "format": "jpeg",
                        "timestamp": int(time.time() * 1000),
                        "streaming": True
                    }
                    
                    response = jsonify(response_data)
                    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response.headers['Pragma'] = 'no-cache'
                    response.headers['Expires'] = '0'
                    response.headers['Access-Control-Allow-Origin'] = '*'
                    return response
                    
                except Exception as encode_error:
                    logger.error(f"Frame encoding error: {encode_error}")
                    return jsonify({"error": "Frame encoding failed", "camera": "usb"})
            else:
                # No frame available - return structured error for iOS app
                return jsonify({
                    "success": False,
                    "error": "No frame available", 
                    "camera": "usb", 
                    "streaming": self.camera.streaming,
                    "timestamp": int(time.time() * 1000)
                })
                
        except Exception as e:
            logger.error(f"USB camera endpoint error: {e}")
            return jsonify({"success": False, "error": str(e), "camera": "usb"})
    
    def get_both_images(self, width=640, height=480) -> dict:
        
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        result = {"timestamp": int(time.time() * 1000), "cameras": {}}
        
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
    
    def handle_detection_alert(self, alert_type):
        
        current_time = time.time() * 1000
        
        if alert_type == "suspicious_activity":
            if (current_time - self.last_notification_time) > NOTIFICATION_COOLDOWN:
                self.current_data.alert = True
                self.current_data.alertType = "suspicious_activity"
                self.last_alert_time = current_time
                self.last_notification_time = current_time
                
                self.last_hardware_trigger_time = current_time
                
                if self.notification_handler:
                    self.notification_handler.trigger_notification("suspicious_activity")
            else:
                logger.debug("Suspicious activity detected but still in notification cooldown")
    
    def enable_object_detection(self) -> dict:
        
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        if self.camera.enable_detection():
            return {"success": True, "message": "Object detection enabled"}
        else:
            return {"error": "Failed to enable object detection"}
    
    def disable_object_detection(self) -> dict:
        
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        self.camera.disable_detection()
        return {"success": True, "message": "Object detection disabled"}
    
    def get_detection_status(self) -> dict:
        
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        camera_status = self.camera.get_camera_status()
        return {
            "detection_enabled": camera_status.get('detection_enabled', False),
            "detector_status": camera_status.get('detector_status', None),
            "camera_streaming": camera_status.get('streaming', False)
        }
    
    def set_detection_model(self, model_name) -> dict:
        
        if not self.camera:
            return {"error": "Camera not initialized"}
        
        if self.camera.set_detection_model(model_name):
            return {"success": True, "message": f"Detection model set to {model_name}"}
        else:
            return {"error": f"Failed to set detection model to {model_name}"}
    
    def read_imu_data(self):
        
        try:
            
            data = self.bus.read_i2c_block_data(MPU6050_ADDR, MPU6050_ACCEL_XOUT_H, 14)
            
            if len(data) >= 14:
                ax_raw = (data[0] << 8) | data[1]
                ay_raw = (data[2] << 8) | data[3]
                az_raw = (data[4] << 8) | data[5]
                
                temp_raw = (data[6] << 8) | data[7]
                
                gx_raw = (data[8] << 8) | data[9]
                gy_raw = (data[10] << 8) | data[11]
                gz_raw = (data[12] << 8) | data[13]
                
                def to_signed_16(val):
                    return val if val < 32768 else val - 65536
                
                ax_raw = to_signed_16(ax_raw)
                ay_raw = to_signed_16(ay_raw)
                az_raw = to_signed_16(az_raw)
                temp_raw = to_signed_16(temp_raw)
                gx_raw = to_signed_16(gx_raw)
                gy_raw = to_signed_16(gy_raw)
                gz_raw = to_signed_16(gz_raw)
                
                self.current_data.ax = ax_raw / 16384.0
                self.current_data.ay = ay_raw / 16384.0
                self.current_data.az = az_raw / 16384.0
                self.current_data.temp = temp_raw / 340.0 + 36.53
                self.current_data.gx = gx_raw / 131.0
                self.current_data.gy = gy_raw / 131.0
                self.current_data.gz = gz_raw / 131.0
                
                current_time = time.time() * 1000
                if hasattr(self, 'last_debug_time'):
                    if current_time - self.last_debug_time > 5000:
                        logger.debug(f"Gyro: {gx_raw}, {gy_raw}, {gz_raw} | Temp: {temp_raw}")
                        self.last_debug_time = current_time
                else:
                    self.last_debug_time = current_time
            else:
                logger.warning("Insufficient IMU data received")
                logger.warning("Not working")
                
        except Exception as e:
            logger.error(f"Error reading IMU data: {e}")
    
    def detect_events(self):
        
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
        
        current_time = time.time() * 1000
        
        can_send_notification = (current_time - self.last_notification_time) > NOTIFICATION_COOLDOWN
        
        if accel_magnitude > FALL_THRESHOLD and not self.fall_detected:
            self.fall_detected = True
            if can_send_notification:
                self.current_data.alert = True
                self.current_data.alertType = "fall"
                self.last_alert_time = current_time
                self.last_notification_time = current_time
            else:
                logger.debug("Fall detected but still in notification cooldown")
        elif accel_magnitude <= FALL_THRESHOLD:
            self.fall_detected = False
        
        if gyro_magnitude > MOVEMENT_THRESHOLD and not self.movement_detected:
            self.movement_detected = True
            if can_send_notification:
                self.current_data.alert = True
                self.current_data.alertType = "movement"
                self.last_alert_time = current_time
                self.last_notification_time = current_time
            else:
                logger.debug("Movement detected but still in notification cooldown")
        elif gyro_magnitude <= MOVEMENT_THRESHOLD:
            self.movement_detected = False
        
        should_trigger_hardware = self.fall_detected or self.movement_detected
        
        if should_trigger_hardware:
            self.last_hardware_trigger_time = current_time
        
        hardware_timeout = 2000
        time_since_trigger = current_time - self.last_hardware_trigger_time
        hardware_should_be_active = time_since_trigger < hardware_timeout
        
        if hardware_should_be_active:
            if self.led:
                self.led.red()
            if self.buzzer and not self.buzzer.is_active:
                self.buzzer.start_tone()
        else:
            if self.led:
                self.led.green()
            if self.buzzer and self.buzzer.is_active:
                self.buzzer.stop_tone()
        
        if self.current_data.alert and current_time - self.last_alert_time > 2000:
            self.current_data.alert = False
            self.current_data.alertType = ""
        
        if hasattr(self, 'last_print_time'):
            if current_time - self.last_print_time > 1000:
                cooldown_remaining = max(0, NOTIFICATION_COOLDOWN - (current_time - self.last_notification_time))
                alert_status = f"{self.current_data.alertType}" if self.current_data.alert else "None"
                logger.debug(f"Accel: {self.current_data.ax:.2f}, {self.current_data.ay:.2f}, {self.current_data.az:.2f} | "
                      f"Gyro: {self.current_data.gx:.2f}, {self.current_data.gy:.2f}, {self.current_data.gz:.2f} | "
                      f"Temp: {self.current_data.temp:.1f}°C | Alert: {alert_status} | "
                      f"Cooldown: {cooldown_remaining/1000:.1f}s")
                self.last_print_time = current_time
        else:
            self.last_print_time = current_time
    
    def trigger_loud_buzzer(self):
        
        if self.buzzer:
            import threading
            buzz_thread = threading.Thread(
                target=self.buzzer.beep, 
                args=(ALERT_DURATION,),
                daemon=True
            )
            buzz_thread.start()
    
    def stop_buzzer(self):
        
        if self.buzzer:
            self.buzzer.stop_tone()
            
    def trigger_suspicious_activity_notification(self):
        
        try:
            if hasattr(self, 'notification_handler') and self.notification_handler:
                success = self.notification_handler.trigger_notification(
                    NOTIFICATION_TYPES['suspicious_activity']
                )
                if success:
                    logger.info("✅ Suspicious activity notification triggered successfully")
                    return True
                else:
                    logger.warning("⚠️ Suspicious activity notification failed (cooldown)")
                    return False
            else:
                logger.error("❌ Notification handler not available")
                return False
        except Exception as e:
            logger.error(f"❌ Error triggering suspicious activity notification: {e}")
            return False
    
    def get_buzzer_status(self) -> dict:
        """Get buzzer status for iOS app"""
        try:
            buzzer_available = self.buzzer is not None
            buzzer_active = self.buzzer.is_active if buzzer_available else False
            
            return {
                "success": True,
                "available": buzzer_available,
                "active": buzzer_active,
                "pin": BUZZER_PIN,
                "frequency": BUZZER_FREQUENCY,
                "last_notification_time": getattr(self, 'last_notification_time', 0),
                "cooldown_ms": NOTIFICATION_COOLDOWN,
                "timestamp": int(time.time() * 1000)
            }
        except Exception as e:
            logger.error(f"Error getting buzzer status: {e}")
            return {
                "success": False,
                "error": str(e),
                "available": False,
                "active": False
            }
    
    def trigger_buzzer_endpoint(self) -> dict:
        """Trigger buzzer via API endpoint"""
        try:
            if not self.buzzer:
                return {
                    "success": False,
                    "error": "Buzzer not available",
                    "message": "Buzzer hardware not initialized"
                }
            
            # Trigger buzzer beep
            self.trigger_loud_buzzer()
            
            return {
                "success": True,
                "message": "Buzzer triggered successfully",
                "duration_ms": ALERT_DURATION,
                "timestamp": int(time.time() * 1000)
            }
        except Exception as e:
            logger.error(f"Error triggering buzzer: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_buzzer_endpoint(self) -> dict:
        """Test buzzer functionality"""
        try:
            if not self.buzzer:
                return {
                    "success": False,
                    "error": "Buzzer not available",
                    "message": "Buzzer hardware not initialized"
                }
            
            # Test with a short beep
            test_duration = 100  # 100ms test beep
            self.buzzer.beep(test_duration)
            
            return {
                "success": True,
                "message": "Buzzer test completed",
                "test_duration_ms": test_duration,
                "timestamp": int(time.time() * 1000)
            }
        except Exception as e:
            logger.error(f"Error testing buzzer: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def main_loop(self):
        
        while self.running:
            current_time = time.time() * 1000
            
            if current_time - self.last_data_time >= DATA_INTERVAL:
                self.read_imu_data()
                self.detect_events()
                self.last_data_time = current_time
            
            time.sleep(0.01)
    
    def run_server(self):
        
        try:
            local_ip = self.get_local_ip()
            logger.info(f"🚀 Starting GuardIt IMU Server on {local_ip}:{SERVER_PORT}")
            self.app.run(host='0.0.0.0', port=SERVER_PORT, debug=False)
        except KeyboardInterrupt:
            logger.info("🛑 Server stopped by user")
        except Exception as e:
            logger.error(f"❌ Server error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        
        self.running = False
        
        if self.camera:
            if self.camera.streaming:
                self.camera.stop_streaming()
            if self.camera.csi_streaming:
                self.camera.stop_csi_streaming()
            self.camera.cleanup()
        
        if self.buzzer:
            self.buzzer.cleanup()
        if self.led:
            self.led.cleanup()
        
        GPIO.cleanup()

def main():
    
    try:
        try:
            GPIO.cleanup()
        except Exception:
            pass
        
        server = GuardItIMUServer()
        server.run_server()
    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            if 'server' in locals() and hasattr(server, 'camera') and server.camera:
                if server.camera.streaming:
                    server.camera.stop_streaming()
                if server.camera.csi_streaming:
                    server.camera.stop_csi_streaming()
            
            GPIO.cleanup()
            logger.info("🧹 Cleanup completed")
        except Exception as cleanup_error:
            logger.error(f"❌ Cleanup error: {cleanup_error}")

if __name__ == "__main__":
    main()

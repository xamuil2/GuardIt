import cv2
import numpy as np
import json
import time
import threading
import subprocess
import os
import signal
import sys
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

class MotionDetector:
    def __init__(self):
        self.detection_enabled = False
        self.last_detection_time = None
        self.detection_threshold = 30
        self.min_area = 500
        self.cooldown_period = 10
        self.camera = None
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=100, varThreshold=40, detectShadows=True
        )
        self.detection_thread = None
        self.running = False
        
    def start_detection(self, camera_type='usb'):
        
        if self.detection_enabled:
            return False
            
        self.detection_enabled = True
        self.running = True
        self.detection_thread = threading.Thread(
            target=self._detection_loop, 
            args=(camera_type,),
            daemon=True
        )
        self.detection_thread.start()
        return True
        
    def stop_detection(self):
        
        self.detection_enabled = False
        self.running = False
        if self.camera:
            self.camera.release()
            self.camera = None
        
    def _detection_loop(self, camera_type):
        
        try:
            if camera_type == 'usb':
                self.camera = cv2.VideoCapture(0)
            elif camera_type == 'csi':
                self.camera = self._setup_csi_camera()
            else:
                return
                
            if not self.camera or not self.camera.isOpened():
                return

            while self.running and self.detection_enabled:
                frame = self._get_frame()
                if frame is not None:
                    motion_detected = self._detect_motion(frame)
                    if motion_detected:
                        self._handle_motion_detected()
                time.sleep(0.1)
                
        except Exception as e:
        finally:
            if self.camera:
                self.camera.release()
                
    def _setup_csi_camera(self):
        
        try:
            cmd = [
                'libcamera-vid',
                '--inline',
                '--nopreview',
                '--width', '640',
                '--height', '480',
                '--framerate', '10',
                '-t', '0',
                '-o', '-'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8
            )
            
            return {'process': process, 'type': 'csi'}
            
        except Exception as e:
            return None
            
    def _get_frame(self):
        
        try:
            if self.camera is None:
                return None
                
            if isinstance(self.camera, dict) and self.camera.get('type') == 'csi':
                return self._get_csi_frame()
            else:
                ret, frame = self.camera.read()
                if ret:
                    return frame
                return None
                
        except Exception as e:
            return None
            
    def _get_csi_frame(self):
        
        try:
            process = self.camera['process']
            
            size_bytes = process.stdout.read(4)
            if len(size_bytes) != 4:
                return None
                
            frame_size = int.from_bytes(size_bytes, byteorder='little')
            
            frame_data = process.stdout.read(frame_size)
            if len(frame_data) != frame_size:
                return None
                
            frame_array = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            
            return frame
            
        except Exception as e:
            return None
            
    def _detect_motion(self, frame):
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            fgmask = self.background_subtractor.apply(gray)
            
            contours, _ = cv2.findContours(
                fgmask, 
                cv2.RETR_EXTERNAL, 
                cv2.CONTOUR_APPROX_SIMPLE
            )
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.min_area:
                    return True
                    
            return False
            
        except Exception as e:
            return False
            
    def _handle_motion_detected(self):
        
        current_time = time.time()
        
        if (self.last_detection_time and 
            current_time - self.last_detection_time < self.cooldown_period):
            return
            
        self.last_detection_time = current_time
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self._save_detection_image()
        
        self._trigger_notification()
        
    def _save_detection_image(self):
        
        try:
            frame = self._get_frame()
            if frame is not None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"detection_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
        except Exception as e:
            
    def _trigger_notification(self):
        
        try:
        except Exception as e:
            
    def get_status(self):
        
        return {
            'enabled': self.detection_enabled,
            'last_detection': self.last_detection_time,
            'threshold': self.detection_threshold,
            'min_area': self.min_area,
            'cooldown_period': self.cooldown_period
        }
        
    def update_settings(self, threshold=None, min_area=None, cooldown=None):
        
        if threshold is not None:
            self.detection_threshold = threshold
        if min_area is not None:
            self.min_area = min_area
        if cooldown is not None:
            self.cooldown_period = cooldown

motion_detector = MotionDetector()

@app.route('/detection/enable', methods=['POST'])
def enable_detection():
    
    try:
        data = request.get_json() or {}
        camera_type = data.get('camera_type', 'usb')
        
        success = motion_detector.start_detection(camera_type)
        return jsonify({
            'success': success,
            'message': 'Detection enabled' if success else 'Failed to enable detection'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/detection/disable', methods=['POST'])
def disable_detection():
    
    try:
        motion_detector.stop_detection()
        return jsonify({
            'success': True,
            'message': 'Detection disabled'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/detection/status', methods=['GET'])
def get_detection_status():
    
    try:
        status = motion_detector.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/detection/settings', methods=['POST'])
def update_detection_settings():
    
    try:
        data = request.get_json() or {}
        motion_detector.update_settings(
            threshold=data.get('threshold'),
            min_area=data.get('min_area'),
            cooldown=data.get('cooldown')
        )
        return jsonify({
            'success': True,
            'message': 'Settings updated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/detection/test', methods=['POST'])
def test_detection():
    
    try:
        motion_detector._handle_motion_detected()
        return jsonify({
            'success': True,
            'message': 'Test detection triggered'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    
    return jsonify({
        'status': 'healthy',
        'detection_enabled': motion_detector.detection_enabled,
        'timestamp': datetime.now().isoformat()
    })

def signal_handler(sig, frame):
    
    motion_detector.stop_detection()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)

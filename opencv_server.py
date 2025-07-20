from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import cv2
import numpy as np
import time
from datetime import datetime
import threading
import os

app = Flask(__name__)
CORS(app)

class CameraServer:
    def __init__(self):
        self.cap = None
        self.is_streaming = False
        self.camera_opened = False
        self.motion_detected = False
        self.last_motion_time = 0
        self.motion_cooldown = 5.0
        self.detection_count = 0
        self.frame_count = 0
        self.start_time = time.time()
        
    def open_camera(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.camera_opened = True
                return True
        return self.camera_opened
    
    def close_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.camera_opened = False
            self.is_streaming = False
    
    def detect_motion(self, frame):
        if frame is None:
            return False
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if not hasattr(self, 'previous_frame'):
            self.previous_frame = gray
            return False
        
        frame_delta = cv2.absdiff(self.previous_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > 500:
                motion_detected = True
                break
        
        self.previous_frame = gray
        return motion_detected
    
    def generate_frames(self):
        if not self.open_camera():
            return
            
        self.is_streaming = True
        
        while self.is_streaming and self.camera_opened:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            frame = cv2.flip(frame, 1)
            
            motion = self.detect_motion(frame)
            if motion:
                current_time = time.time()
                if current_time - self.last_motion_time > self.motion_cooldown:
                    self.motion_detected = True
                    self.last_motion_time = current_time
                    self.detection_count += 1
            else:
                self.motion_detected = False
            
            self.frame_count += 1
            
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

camera_server = CameraServer()

@app.route('/status')
def status():
    return jsonify({
        'camera_opened': camera_server.camera_opened,
        'is_streaming': camera_server.is_streaming,
        'motion_detected': camera_server.motion_detected,
        'detection_count': camera_server.detection_count,
        'frame_count': camera_server.frame_count,
        'uptime': time.time() - camera_server.start_time
    })

@app.route('/start')
def start_camera():
    if camera_server.open_camera():
        return jsonify({'success': True, 'message': 'Camera started'})
    else:
        return jsonify({'success': False, 'message': 'Failed to open camera'})

@app.route('/stop')
def stop_camera():
    camera_server.close_camera()
    return jsonify({'success': True, 'message': 'Camera stopped'})

@app.route('/detect')
def detect_motion():
    return jsonify({
        'motion_detected': camera_server.motion_detected,
        'detection_count': camera_server.detection_count,
        'last_motion_time': camera_server.last_motion_time
    })

@app.route('/settings')
def get_settings():
    if request.method == 'GET':
        return jsonify({
            'fps': 30,
            'resolution': '640x480',
            'quality': 80,
            'motion_threshold': 500,
            'motion_cooldown': camera_server.motion_cooldown
        })
    elif request.method == 'POST':
        data = request.json
        if 'motion_cooldown' in data:
            camera_server.motion_cooldown = data['motion_cooldown']
        return jsonify({'success': True})

@app.route('/stats')
def get_stats():
    return jsonify({
        'detection_model_loaded': True,
        'active_tracks': camera_server.detection_count,
        'camera_settings': {
            'fps': 30,
            'resolution': '640x480'
        },
        'total_detections': camera_server.detection_count,
        'total_frames': camera_server.frame_count
    })

@app.route('/screenshot')
def take_screenshot():
    if camera_server.cap is not None and camera_server.camera_opened:
        ret, frame = camera_server.cap.read()
        if ret:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.jpg"
            
            try:
                cv2.imwrite(filename, frame)
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'timestamp': timestamp
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'Camera not available'})

@app.route('/stream')
def video_stream():
    return Response(camera_server.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>GuardIt Camera Server</title>
            <style>
                body { 
                    margin: 0; 
                    background: #000; 
                    font-family: Arial, sans-serif;
                    color: white;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .status {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
                img { 
                    width: 100%; 
                    max-width: 640px;
                    height: auto;
                    border-radius: 10px;
                }
                .controls {
                    margin: 20px 0;
                }
                button {
                    background: #ff4444;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    margin: 5px;
                    cursor: pointer;
                }
                button:hover {
                    background: #ff6666;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>GuardIt Camera Server</h1>
                <div class="status">
                    <h3>Server Status</h3>
                    <p>Camera: <span id="camera-status">Checking...</span></p>
                    <p>Streaming: <span id="streaming-status">Checking...</span></p>
                    <p>Motion: <span id="motion-status">Checking...</span></p>
                </div>
                <div class="controls">
                    <button onclick="startCamera()">Start Camera</button>
                    <button onclick="stopCamera()">Stop Camera</button>
                    <button onclick="takeScreenshot()">Take Screenshot</button>
                </div>
                <img src="/stream" alt="Camera Feed" id="camera-feed" style="display: none;" />
            </div>
            
            <script>
                function updateStatus() {
                    fetch('/status')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('camera-status').textContent = data.camera_opened ? 'Open' : 'Closed';
                            document.getElementById('streaming-status').textContent = data.is_streaming ? 'Active' : 'Inactive';
                            document.getElementById('motion-status').textContent = data.motion_detected ? 'Detected' : 'None';
                            
                            if (data.is_streaming) {
                                document.getElementById('camera-feed').style.display = 'block';
                            } else {
                                document.getElementById('camera-feed').style.display = 'none';
                            }
                        });
                }
                
                function startCamera() {
                    fetch('/start')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                updateStatus();
                            }
                        });
                }
                
                function stopCamera() {
                    fetch('/stop')
                        .then(response => response.json())
                        .then(data => {
                            updateStatus();
                        });
                }
                
                function takeScreenshot() {
                    fetch('/screenshot')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                alert('Screenshot saved: ' + data.filename);
                            } else {
                                alert('Failed to take screenshot');
                            }
                        });
                }
                
                setInterval(updateStatus, 2000);
                updateStatus();
            </script>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) 
#!/usr/bin/env python3
"""
Simple Camera Server for GuardIt
This version bypasses complex authorization and works better on macOS
"""

from flask import Flask, Response, jsonify, render_template_string
from flask_cors import CORS
import cv2
import time
import os

app = Flask(__name__)
CORS(app)

class SimpleCameraServer:
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
            # Try different camera indices
            for i in range(3):
                self.cap = cv2.VideoCapture(i)
                if self.cap.isOpened():
                    print(f"✅ Camera opened successfully on index {i}")
                    self.camera_opened = True
                    return True
                else:
                    self.cap.release()
                    self.cap = None
            
            # If no camera found, create a test pattern
            print("⚠️ No camera found, creating test pattern")
            self.camera_opened = True
            return True
        return self.camera_opened
    
    def close_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.camera_opened = False
            self.is_streaming = False
    
    def create_test_frame(self):
        """Create a test frame when no camera is available"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, "GuardIt Camera", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        cv2.putText(frame, "Test Pattern", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        cv2.putText(frame, f"Time: {time.strftime('%H:%M:%S')}", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "Camera not available", (50, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        return frame
    
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
            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    frame = self.create_test_frame()
            else:
                frame = self.create_test_frame()
            
            frame = cv2.flip(frame, 1)
            
            # Simple motion detection
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
            
            # Add status text to frame
            cv2.putText(frame, f"Motion: {'YES' if self.motion_detected else 'NO'}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if not self.motion_detected else (0, 0, 255), 2)
            cv2.putText(frame, f"Detections: {self.detection_count}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

camera_server = SimpleCameraServer()

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>GuardIt Camera Feed</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                margin: 0; 
                padding: 0; 
                background: #000; 
                font-family: Arial, sans-serif;
                color: white;
                display: flex;
                flex-direction: column;
                height: 100vh;
            }
            .header {
                background: rgba(255, 68, 68, 0.2);
                padding: 15px;
                text-align: center;
                border-bottom: 2px solid #ff4444;
            }
            .header h1 {
                margin: 0;
                font-size: 24px;
                color: #ff4444;
            }
            .status {
                background: rgba(255, 255, 255, 0.1);
                padding: 10px;
                text-align: center;
                font-size: 14px;
            }
            .camera-container {
                flex: 1;
                display: flex;
                justify-content: center;
                align-items: center;
                position: relative;
            }
            .camera-feed {
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
                border: 2px solid #ff4444;
                border-radius: 10px;
            }
            .controls {
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                text-align: center;
            }
            .btn {
                background: #ff4444;
                color: white;
                border: none;
                padding: 10px 20px;
                margin: 5px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            .btn:hover {
                background: #ff6666;
            }
            .motion-alert {
                position: absolute;
                top: 20px;
                right: 20px;
                background: rgba(255, 0, 0, 0.8);
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                display: none;
                animation: pulse 1s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔒 GuardIt Security Camera</h1>
        </div>
        
        <div class="status" id="status">
            Connecting to camera...
        </div>
        
        <div class="camera-container">
            <img src="/video_feed" alt="Camera Feed" class="camera-feed" id="camera-feed" />
            <div class="motion-alert" id="motion-alert">
                🚨 MOTION DETECTED!
            </div>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="refreshCamera()">🔄 Refresh</button>
            <button class="btn" onclick="takeScreenshot()">📸 Screenshot</button>
            <button class="btn" onclick="toggleFullscreen()">⛶ Fullscreen</button>
        </div>
        
        <script>
            function updateStatus() {
                fetch('/status')
                    .then(response => response.json())
                    .then(data => {
                        const statusEl = document.getElementById('status');
                        const motionAlert = document.getElementById('motion-alert');
                        
                        statusEl.innerHTML = `
                            Camera: ${data.camera_opened ? '✅ Connected' : '❌ Disconnected'} | 
                            Streaming: ${data.is_streaming ? '✅ Active' : '❌ Inactive'} | 
                            Motion: ${data.motion_detected ? '🚨 Detected' : '✅ None'} | 
                            Detections: ${data.detection_count}
                        `;
                        
                        if (data.motion_detected) {
                            motionAlert.style.display = 'block';
                        } else {
                            motionAlert.style.display = 'none';
                        }
                    })
                    .catch(error => {
                        document.getElementById('status').innerHTML = '❌ Connection Error';
                    });
            }
            
            function refreshCamera() {
                const img = document.getElementById('camera-feed');
                img.src = '/video_feed?' + new Date().getTime();
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
            
            function toggleFullscreen() {
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen();
                } else {
                    document.exitFullscreen();
                }
            }
            
            // Update status every 2 seconds
            setInterval(updateStatus, 2000);
            updateStatus();
            
            // Refresh camera feed if it fails to load
            document.getElementById('camera-feed').onerror = function() {
                setTimeout(refreshCamera, 1000);
            };
        </script>
    </body>
    </html>
    ''')

@app.route('/video_feed')
def video_feed():
    return Response(camera_server.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

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

@app.route('/screenshot')
def take_screenshot():
    if camera_server.cap is not None and camera_server.camera_opened:
        ret, frame = camera_server.cap.read()
        if ret:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
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

if __name__ == '__main__':
    import numpy as np
    
    print("🚀 Starting Simple GuardIt Camera Server...")
    print("📱 Your phone should connect to: http://172.20.10.8:8090")
    print("🌐 Open in Safari: http://172.20.10.8:8090")
    print("📋 Make sure your camera is connected and accessible")
    print("\n🔧 Server controls:")
    print("   - Press Ctrl+C to stop the server")
    print("   - Open http://localhost:8090 in your browser to test")
    print("\n" + "="*50)
    
    app.run(host='0.0.0.0', port=8090, debug=True, threaded=True) 
from flask import Flask, Response, render_template_string, jsonify, request
from flask_cors import CORS
import cv2
import numpy as np
import time
from datetime import datetime
import sys
import os
import socket
sys.path.append('.')

from detector import MultiModelPersonDetector

app = Flask(__name__)
CORS(app)

detector = MultiModelPersonDetector()

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

camera_server = CameraServer()

def gen_frames():
    if not camera_server.open_camera():
        return
        
    camera_server.is_streaming = True
    
    while camera_server.is_streaming and camera_server.camera_opened:
        ret, frame = camera_server.cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        boxes, weights = detector.detect_people(frame)
        detector.detection_count += len(boxes)
        frame_center = (frame.shape[0], frame.shape[1])
        alerts = detector.track_movement(boxes, frame_center)
        if alerts is None:
            alerts = []
        current_time = time.time()
        if alerts and current_time - detector.last_alert_time > detector.alert_cooldown:
            detector.last_alert_time = current_time
            detector.trigger_notification("Suspicious behavior detected!")
            camera_server.motion_detected = True
            camera_server.last_motion_time = current_time
            camera_server.detection_count += 1
        else:
            camera_server.motion_detected = False
            
        frame = detector.draw_detections(frame, boxes, alerts)
        camera_server.frame_count += 1
        
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

HTML_PAGE = '''
<html>
  <head>
    <title>Camera Feed</title>
    <style>
      body { margin: 0; background: #000; }
      img { width: 100vw; height: 100vh; object-fit: contain; display: block; margin: 0 auto; }
    </style>
  </head>
  <body>
    <img src="/video_feed" alt="Camera Feed" />
  </body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

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
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "Unable to determine IP"

if __name__ == '__main__':
    local_ip = get_local_ip()
    port = 8090

    print("Starting GuardIt Camera Server...")
    print(f"Server will be available at:")
    print(f"  Local access: http://localhost:{port}")
    print(f"  Network access: http://{local_ip}:{port}")
    print("Make sure your camera is connected and accessible")
    print("Access /video_feed for the camera stream")
    print("Press CTRL+C to stop the server")

    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)

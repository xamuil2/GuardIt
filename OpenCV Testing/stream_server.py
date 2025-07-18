from flask import Flask, Response, render_template_string
from flask_cors import CORS
import cv2
import numpy as np
import time
from datetime import datetime
import sys
sys.path.append('.')

from detector import MultiModelPersonDetector

app = Flask(__name__)
CORS(app)

detector = MultiModelPersonDetector()

def gen_frames():
    detector = MultiModelPersonDetector()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    while True:
        ret, frame = cap.read()
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
        frame = detector.draw_detections(frame, boxes, alerts)
        # Remove BGR to RGB conversion - keep original colors
        ret, buffer = cv2.imencode('.jpg', frame)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090, debug=True)

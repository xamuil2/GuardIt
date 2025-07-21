from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import cv2
import threading
import time
import os
import sys

app = Flask(__name__)
CORS(app)

camera = None
is_streaming = False
stream_thread = None
camera_status = {
    'csi_camera_available': False,
    'usb_camera_available': False,
    'is_streaming': False,
    'current_camera': None,
    'stream_quality': 80,
    'stream_width': 640,
    'stream_height': 480
}

def check_camera_availability():
    global camera_status
    
    csi_camera = cv2.VideoCapture(0)
    if csi_camera.isOpened():
        camera_status['csi_camera_available'] = True
        csi_camera.release()
    
    usb_camera = cv2.VideoCapture(2)
    if usb_camera.isOpened():
        camera_status['usb_camera_available'] = True
        usb_camera.release()

def get_camera(camera_type='usb'):
    if camera_type == 'csi':
        return cv2.VideoCapture(0)
    else:
        return cv2.VideoCapture(2)

def generate_frames(camera_type='usb', quality=80, width=640, height=480):
    global camera, is_streaming
    
    camera = get_camera(camera_type)
    if not camera.isOpened():
        return
    
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    is_streaming = True
    camera_status['is_streaming'] = True
    camera_status['current_camera'] = camera_type
    camera_status['stream_quality'] = quality
    camera_status['stream_width'] = width
    camera_status['stream_height'] = height
    
    try:
        while is_streaming:
            ret, frame = camera.read()
            if not ret:
                break
            
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            ret, buffer = cv2.imencode('.jpg', frame, encode_param)
            
            if ret:
                frame_data = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
            
            time.sleep(0.033)
    finally:
        if camera:
            camera.release()
        is_streaming = False
        camera_status['is_streaming'] = False

@app.route('/')
def index():
    return jsonify({
        'title': 'Simple Camera Server',
        'version': '1.0.0',
        'endpoints': {
            'camera': '/camera/<type>',
            'stream': '/stream/<type>',
            'status': '/status',
            'start': '/stream/start',
            'stop': '/stream/stop'
        }
    })

@app.route('/camera/<camera_type>')
def get_camera_frame(camera_type):
    global camera
    
    if camera_type not in ['csi', 'usb']:
        return jsonify({'error': 'Invalid camera type'}), 400
    
    if not camera_status[f'{camera_type}_camera_available']:
        return jsonify({'error': f'{camera_type.upper()} camera not available'}), 503
    
    try:
        temp_camera = get_camera(camera_type)
        if not temp_camera.isOpened():
            return jsonify({'error': f'Failed to open {camera_type} camera'}), 503
        
        ret, frame = temp_camera.read()
        temp_camera.release()
        
        if not ret:
            return jsonify({'error': 'Failed to capture frame'}), 503
        
        quality = int(request.args.get('quality', 80))
        width = int(request.args.get('width', 640))
        height = int(request.args.get('height', 480))
        
        frame = cv2.resize(frame, (width, height))
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        ret, buffer = cv2.imencode('.jpg', frame, encode_param)
        
        if ret:
            response = Response(buffer.tobytes(), mimetype='image/jpeg')
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        else:
            return jsonify({'error': 'Failed to encode frame'}), 503
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream/<camera_type>')
def stream_camera(camera_type):
    if camera_type not in ['csi', 'usb']:
        return jsonify({'error': 'Invalid camera type'}), 400
    
    if not camera_status[f'{camera_type}_camera_available']:
        return jsonify({'error': f'{camera_type.upper()} camera not available'}), 503
    
    quality = int(request.args.get('quality', 80))
    width = int(request.args.get('width', 640))
    height = int(request.args.get('height', 480))
    
    return Response(
        generate_frames(camera_type, quality, width, height),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/stream/raw')
def stream_raw():
    global camera
    
    if not camera_status['usb_camera_available'] and not camera_status['csi_camera_available']:
        return jsonify({'error': 'No camera available'}), 503
    
    camera_type = camera_status.get('current_camera', 'usb')
    quality = camera_status.get('stream_quality', 80)
    width = camera_status.get('stream_width', 640)
    height = camera_status.get('stream_height', 480)
    
    return Response(
        generate_frames(camera_type, quality, width, height),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/stream/start', methods=['POST'])
def start_stream():
    global stream_thread
    
    if is_streaming:
        return jsonify({'message': 'Stream already running'})
    
    data = request.get_json() or {}
    camera_type = data.get('camera', 'usb')
    quality = data.get('quality', 80)
    width = data.get('width', 640)
    height = data.get('height', 480)
    
    if camera_type not in ['csi', 'usb']:
        return jsonify({'error': 'Invalid camera type'}), 400
    
    if not camera_status[f'{camera_type}_camera_available']:
        return jsonify({'error': f'{camera_type.upper()} camera not available'}), 503
    
    stream_thread = threading.Thread(
        target=generate_frames,
        args=(camera_type, quality, width, height)
    )
    stream_thread.daemon = True
    stream_thread.start()
    
    return jsonify({'message': 'Stream started successfully'})

@app.route('/stream/stop', methods=['POST'])
def stop_stream():
    global is_streaming, camera
    
    is_streaming = False
    if camera:
        camera.release()
        camera = None
    
    return jsonify({'message': 'Stream stopped successfully'})

@app.route('/status')
def get_status():
    return jsonify(camera_status)

if __name__ == '__main__':
    check_camera_availability()
    
    port = int(os.environ.get('PORT', 8090))
    host = os.environ.get('HOST', '0.0.0.0')

    app.run(host=host, port=port, debug=True, threaded=True)

# GuardIt OpenCV Camera Integration Setup Guide

This guide will help you set up the OpenCV camera server on your laptop and connect it to your GuardIt React Native app for live camera streaming and person detection.

## 🎯 Overview

The integration consists of:
1. **OpenCV Server** (runs on your laptop) - Provides camera streaming and person detection
2. **React Native App** (runs on your phone) - Displays the camera feed and receives alerts

## 📋 Prerequisites

- Python 3.7 or higher installed on your laptop
- Webcam access on your laptop
- Both devices connected to the same WiFi network
- GuardIt React Native app installed on your phone

## 🚀 Quick Setup

### Step 1: Install Dependencies

Navigate to the OpenCV server directory and install Python dependencies:

```bash
cd opencv_server
pip install -r requirements.txt
```

### Step 2: Download YOLOv8 Model

Download the person detection model:

```bash
# Option 1: Using wget
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

# Option 2: Using curl
curl -L https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -o yolov8n.pt

# Option 3: Copy from existing folder (if available)
cp "../OpenCV Testing/yolov8n.pt" .
```

### Step 3: Find Your IP Address

Run the IP finder script:

```bash
python get_ip.py
```

Note the IP address displayed (e.g., `192.168.1.100`).

### Step 4: Start the OpenCV Server

Start the camera server:

```bash
python start_server.py
```

You should see output like:
```
🚀 GuardIt OpenCV Camera Server
==================================================
✅ All dependencies are installed
✅ YOLOv8 model found: yolov8n.pt
✅ Camera is accessible
🌐 Local IP address: 192.168.1.100
📱 React Native app should connect to: 192.168.1.100:5000
```

### Step 5: Connect from Mobile App

1. Open the GuardIt app on your phone
2. Tap "VIEW FEED" on the home screen
3. Enter your laptop's IP address (e.g., `192.168.1.100`)
4. Tap "Connect to Server"
5. Tap "Start Stream" to view the live camera feed

## 🔧 Advanced Configuration

### Camera Settings

You can adjust camera settings via the server API:

```bash
# Get current settings
curl http://192.168.1.100:5000/settings

# Update settings
curl -X POST http://192.168.1.100:5000/settings \
  -H "Content-Type: application/json" \
  -d '{"fps": 15, "brightness": 60}'
```

### Detection Parameters

The server automatically detects:
- **Approaching behavior**: When someone gets closer to the camera
- **Pacing behavior**: When someone walks back and forth repeatedly

### Performance Optimization

For better performance:
- Lower FPS setting (15-20 instead of 30)
- Reduce resolution if needed
- Close other applications using the camera
- Ensure good WiFi signal strength

## 🛠️ Troubleshooting

### Camera Not Accessible

**Problem**: Camera fails to open or no video feed

**Solutions**:
- Check if webcam is connected and working
- Close other applications using the camera (Zoom, Teams, etc.)
- Try restarting the server
- Check camera permissions on your operating system

### Connection Failed

**Problem**: Mobile app can't connect to server

**Solutions**:
- Ensure both devices are on the same WiFi network
- Check firewall settings (allow port 5000)
- Verify the IP address is correct
- Try disabling antivirus temporarily
- Check if the server is running (`python start_server.py`)

### YOLOv8 Model Not Found

**Problem**: Person detection is disabled

**Solutions**:
- Download the model file using the commands above
- Place `yolov8n.pt` in the same directory as the server
- The server will work without detection if the model is missing

### Poor Video Quality

**Problem**: Video is choppy or low quality

**Solutions**:
- Reduce FPS setting in camera settings
- Lower resolution if needed
- Check network bandwidth
- Move closer to WiFi router
- Close other network-intensive applications

### High CPU Usage

**Problem**: Server uses too much CPU

**Solutions**:
- Lower FPS setting
- Reduce resolution
- Disable person detection if not needed
- Close other applications
- Use a more powerful computer

## 📱 Mobile App Features

Once connected, your mobile app will have access to:

- **Live Camera Stream**: Real-time video feed from your laptop's webcam
- **Person Detection**: Shows bounding boxes around detected people
- **Motion Alerts**: Notifications when suspicious behavior is detected
- **Detection Statistics**: Shows YOLOv8 model status and active tracks
- **Screenshot Capture**: Take screenshots of the current camera view
- **Camera Controls**: Start/stop streaming and adjust settings

## 🔒 Security Considerations

- The server runs on your local network only
- No authentication is implemented (for local use only)
- Keep your WiFi network secure
- Consider using HTTPS for production deployments
- Camera only streams when explicitly started

## 📊 API Endpoints

The OpenCV server provides these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server information |
| `/status` | GET | Camera and server status |
| `/start` | GET | Start camera stream |
| `/stop` | GET | Stop camera stream |
| `/stream` | GET | Live camera stream (MJPEG) |
| `/detect` | GET | Motion detection status |
| `/settings` | GET/POST | Camera settings |
| `/screenshot` | GET | Take a screenshot |

## 🆘 Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all dependencies are installed
3. Check the server logs for error messages
4. Ensure your webcam works with other applications
5. Test network connectivity between devices

## 📝 Development Notes

### Adding New Features

The server is designed to be extensible. You can:
- Add new detection models
- Implement custom alert types
- Add video recording capabilities
- Integrate with home automation systems

### Customization

Key files to modify:
- `camera_stream.py` - Main server logic
- `start_server.py` - Startup and configuration
- `requirements.txt` - Python dependencies

## 🎉 Success!

Once everything is working, you should see:
- Live camera feed in your mobile app
- Person detection with bounding boxes
- Motion alerts for suspicious behavior
- Real-time detection statistics

Your GuardIt security system is now fully operational! 🚀 
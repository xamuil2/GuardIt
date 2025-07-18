<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Raspberry Pi IoT Project Instructions

This is a Raspberry Pi 4B IoT project that includes:
- MPU-9250 IMU sensor data collection via I2C
- RGB LED and passive buzzer control via GPIO
- Dual camera streaming (CSI camera and USB webcam)
- FastAPI web server for iOS app communication
- WebSocket support for real-time data streaming

## Hardware Configuration
- Raspberry Pi 4B running Raspberry Pi OS
- MPU-9250 IMU connected via I2C (default pins: SDA=GPIO2, SCL=GPIO3)
- RGB LED connected to GPIO pins (configurable)
- Passive buzzer connected to GPIO pin (configurable)
- CSI camera module
- USB webcam

## Key Libraries
- FastAPI for web server and API endpoints
- uvicorn for ASGI server
- RPi.GPIO for GPIO control
- smbus2 for I2C communication
- opencv-python for camera handling
- websockets for real-time communication
- asyncio for asynchronous operations

## Code Style
- Use async/await patterns for non-blocking operations
- Implement proper error handling and logging
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Structure code with clear separation of concerns

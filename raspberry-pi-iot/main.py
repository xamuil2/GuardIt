import asyncio
import logging
import json
from contextlib import asynccontextmanager
from typing import Dict, Any
import uvicorn

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.mpu9250 import MPU9250
from src.hardware_controller import HardwareController, Colors, Notes
from src.camera_manager import CameraManager
from config import ServerConfig, SensorConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

imu_sensor = None
hardware_controller = None
camera_manager = None
websocket_clients = set()

class LEDRequest(BaseModel):
    red: int = 0
    green: int = 0
    blue: int = 0
    brightness: float = 1.0
    hex_color: str = None

class BuzzerRequest(BaseModel):
    frequency: int = 1000
    duration: float = 0.5
    count: int = 1

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting IoT device server...")
    
    global imu_sensor, hardware_controller, camera_manager
    
    imu_sensor = MPU9250()
    if not await imu_sensor.initialize():
        logger.warning("Failed to initialize MPU-9250 sensor")
    
    hardware_controller = HardwareController()
    if not await hardware_controller.initialize():
        logger.warning("Failed to initialize hardware controller")
    
    camera_manager = CameraManager()
    if not await camera_manager.initialize():
        logger.warning("Failed to initialize camera manager")
    
    camera_manager.start_streaming('csi')
    camera_manager.start_streaming('usb')
    
    asyncio.create_task(broadcast_sensor_data())
    
    logger.info("IoT device server startup complete")
    
    yield
    
    logger.info("Shutting down IoT device server...")
    
    if imu_sensor:
        imu_sensor.close()
    
    if hardware_controller:
        hardware_controller.cleanup()
    
    if camera_manager:
        camera_manager.cleanup()

app = FastAPI(
    title="Raspberry Pi IoT Device",
    description="IoT device with IMU sensor, cameras, LED, and buzzer control",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def broadcast_sensor_data():
    
    while True:
        try:
            if imu_sensor and imu_sensor.is_initialized and websocket_clients:
                sensor_data = await imu_sensor.read_all_sensors()
                if sensor_data:
                    message = json.dumps({
                        "type": "sensor_data",
                        "data": sensor_data
                    })
                    
                    disconnected_clients = set()
                    for client in websocket_clients:
                        try:
                            await client.send_text(message)
                        except Exception:
                            disconnected_clients.add(client)
                    
                    websocket_clients -= disconnected_clients
            
            await asyncio.sleep(1.0 / SensorConfig.IMU_SAMPLE_RATE)
            
        except Exception as e:
            logger.error(f"Error broadcasting sensor data: {e}")
            await asyncio.sleep(1.0)

@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Raspberry Pi IoT Device</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .status { margin: 20px 0; }
            .online { color: green; }
            .offline { color: red; }
        </style>
    </head>
    <body>
        <h1>Raspberry Pi IoT Device</h1>
        <h2>System Status</h2>
        <div class="status">
            <strong>Server:</strong> <span class="online">Online</span>
        </div>
        <div class="status">
            <strong>IMU Sensor:</strong> 
            <span class="{imu_status_class}">{imu_status}</span>
        </div>
        <div class="status">
            <strong>Hardware Controller:</strong> 
            <span class="{hw_status_class}">{hw_status}</span>
        </div>
        <div class="status">
            <strong>Camera Manager:</strong> 
            <span class="{cam_status_class}">{cam_status}</span>
        </div>
        
        <h2>API Endpoints</h2>
        <ul>
            <li><a href="/docs">API Documentation</a></li>
            <li><a href="/imu">IMU Sensor Data</a></li>
            <li><a href="/camera/info">Camera Information</a></li>
            <li><a href="/camera/csi/stream">CSI Camera Stream</a></li>
            <li><a href="/camera/usb/stream">USB Camera Stream</a></li>
        </ul>
        
        <h2>WebSocket</h2>
        <p>Real-time sensor data: <code>ws://{{host}}/ws</code></p>
    </body>
    </html>
    """.format(
        imu_status="Online" if imu_sensor and imu_sensor.is_initialized else "Offline",
        imu_status_class="online" if imu_sensor and imu_sensor.is_initialized else "offline",
        hw_status="Online" if hardware_controller and hardware_controller.is_initialized else "Offline",
        hw_status_class="online" if hardware_controller and hardware_controller.is_initialized else "offline",
        cam_status="Online" if camera_manager else "Offline",
        cam_status_class="online" if camera_manager else "offline"
    )
    
    return html_content

@app.get("/imu")
async def get_imu_data():
    if not imu_sensor or not imu_sensor.is_initialized:
        raise HTTPException(status_code=503, detail="IMU sensor not available")
    
    try:
        data = await imu_sensor.read_all_sensors()
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        logger.error(f"Error reading IMU data: {e}")
        raise HTTPException(status_code=500, detail="Failed to read IMU data")

@app.post("/led")
async def control_led(request: LEDRequest):
    
    if not hardware_controller or not hardware_controller.is_initialized:
        raise HTTPException(status_code=503, detail="Hardware controller not available")
    
    try:
        if request.hex_color:
            await hardware_controller.set_led_hex(request.hex_color, request.brightness)
        else:
            await hardware_controller.set_led_color(
                request.red, request.green, request.blue, request.brightness
            )
        
        return {
            "status": "success",
            "message": "LED color updated"
        }
    except Exception as e:
        logger.error(f"Error controlling LED: {e}")
        raise HTTPException(status_code=500, detail="Failed to control LED")

@app.post("/led/off")
async def turn_off_led():
    
    if not hardware_controller or not hardware_controller.is_initialized:
        raise HTTPException(status_code=503, detail="Hardware controller not available")
    
    try:
        await hardware_controller.led_off()
        return {
            "status": "success",
            "message": "LED turned off"
        }
    except Exception as e:
        logger.error(f"Error turning off LED: {e}")
        raise HTTPException(status_code=500, detail="Failed to turn off LED")

@app.get("/led/status")
async def get_led_status():
    
    if not hardware_controller or not hardware_controller.is_initialized:
        raise HTTPException(status_code=503, detail="Hardware controller not available")
    
    try:
        led_status = await hardware_controller.get_led_status()
        return {
            "status": "success",
            "led": led_status
        }
    except Exception as e:
        logger.error(f"Error getting LED status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get LED status")

@app.post("/buzzer")
async def control_buzzer(request: BuzzerRequest):
    
    if not hardware_controller or not hardware_controller.is_initialized:
        raise HTTPException(status_code=503, detail="Hardware controller not available")
    
    try:
        if request.count > 1:
            await hardware_controller.buzzer_beep(
                count=request.count,
                frequency=request.frequency,
                duration=request.duration
            )
        else:
            await hardware_controller.play_buzzer_tone(
                request.frequency, request.duration
            )
        
        return {
            "status": "success",
            "message": f"Buzzer played at {request.frequency}Hz for {request.duration}s"
        }
    except Exception as e:
        logger.error(f"Error controlling buzzer: {e}")
        raise HTTPException(status_code=500, detail="Failed to control buzzer")

@app.get("/buzzer/status")
async def get_buzzer_status():
    
    if not hardware_controller or not hardware_controller.is_initialized:
        raise HTTPException(status_code=503, detail="Hardware controller not available")
    
    try:
        buzzer_status = await hardware_controller.get_buzzer_status()
        return {
            "status": "success",
            "buzzer": buzzer_status
        }
    except Exception as e:
        logger.error(f"Error getting buzzer status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get buzzer status")

@app.get("/camera/info")
async def get_camera_info():
    
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not available")
    
    return {
        "status": "success",
        "cameras": camera_manager.get_all_camera_info()
    }

@app.get("/camera/{camera_type}/stream")
async def stream_camera(camera_type: str):
    
    if camera_type not in ['csi', 'usb']:
        raise HTTPException(status_code=400, detail="Invalid camera type")
    
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not available")
    
    if not camera_manager.is_streaming[camera_type]:
        raise HTTPException(status_code=503, detail=f"{camera_type} camera not streaming")
    
    return StreamingResponse(
        camera_manager.generate_mjpeg_stream(camera_type),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    
    await websocket.accept()
    websocket_clients.add(websocket)
    logger.info(f"WebSocket client connected. Total clients: {len(websocket_clients)}")
    
    try:
        status_message = {
            "type": "status",
            "data": {
                "imu_available": imu_sensor and imu_sensor.is_initialized,
                "hardware_available": hardware_controller and hardware_controller.is_initialized,
                "cameras": camera_manager.get_all_camera_info() if camera_manager else {}
            }
        }
        await websocket.send_text(json.dumps(status_message))
        
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                if data.get("type") == "led_control":
                    led_data = data.get("data", {})
                    if hardware_controller and hardware_controller.is_initialized:
                        await hardware_controller.set_led_color(
                            led_data.get("red", 0),
                            led_data.get("green", 0),
                            led_data.get("blue", 0),
                            led_data.get("brightness", 1.0)
                        )
                
                elif data.get("type") == "buzzer_control":
                    buzzer_data = data.get("data", {})
                    if hardware_controller and hardware_controller.is_initialized:
                        await hardware_controller.play_buzzer_tone(
                            buzzer_data.get("frequency", 1000),
                            buzzer_data.get("duration", 0.5)
                        )
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    
    finally:
        websocket_clients.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(websocket_clients)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=ServerConfig.HOST,
        port=ServerConfig.PORT,
        reload=ServerConfig.DEBUG,
        log_level="info"
    )

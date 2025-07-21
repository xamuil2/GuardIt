import RPi.GPIO as GPIO
import time
import asyncio
import logging
from typing import Tuple, Optional
from config import GPIOConfig

logger = logging.getLogger(__name__)

class HardwareController:

    def __init__(self):
        
        self.is_initialized = False
        self.led_pwm = {}
        self.buzzer_pwm = None
        self.current_led_state = {'red': 0, 'green': 0, 'blue': 0, 'brightness': 0.0, 'is_on': False}
        self.current_buzzer_state = {'is_active': False, 'frequency': 0, 'start_time': None, 'duration': 0}
        
    async def initialize(self) -> bool:
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            GPIO.setup(GPIOConfig.LED_RED_PIN, GPIO.OUT)
            GPIO.setup(GPIOConfig.LED_GREEN_PIN, GPIO.OUT)
            GPIO.setup(GPIOConfig.LED_BLUE_PIN, GPIO.OUT)
            
            GPIO.setup(GPIOConfig.BUZZER_PIN, GPIO.OUT)
            
            self.led_pwm['red'] = GPIO.PWM(GPIOConfig.LED_RED_PIN, 1000)
            self.led_pwm['green'] = GPIO.PWM(GPIOConfig.LED_GREEN_PIN, 1000)
            self.led_pwm['blue'] = GPIO.PWM(GPIOConfig.LED_BLUE_PIN, 1000)
            
            for pwm in self.led_pwm.values():
                pwm.start(0)
            
            self.buzzer_pwm = GPIO.PWM(GPIOConfig.BUZZER_PIN, 1000)
            self.buzzer_pwm.start(0)
            
            self.is_initialized = True
            logger.info("Hardware controller initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize hardware controller: {e}")
            return False
    
    async def set_led_color(self, red: int, green: int, blue: int, brightness: float = 1.0):
        
        if not self.is_initialized:
            raise RuntimeError("Hardware controller not initialized")
        
        try:
            red = max(0, min(255, red))
            green = max(0, min(255, green))
            blue = max(0, min(255, blue))
            brightness = max(0.0, min(1.0, brightness))
            
            red_duty = (red / 255.0) * brightness * 100
            green_duty = (green / 255.0) * brightness * 100
            blue_duty = (blue / 255.0) * brightness * 100
            
            self.led_pwm['red'].ChangeDutyCycle(red_duty)
            self.led_pwm['green'].ChangeDutyCycle(green_duty)
            self.led_pwm['blue'].ChangeDutyCycle(blue_duty)
            
            self.current_led_state = {
                'red': red,
                'green': green,
                'blue': blue,
                'brightness': brightness,
                'is_on': (red > 0 or green > 0 or blue > 0) and brightness > 0
            }
            
            logger.debug(f"LED color set to RGB({red}, {green}, {blue}) at {brightness*100:.1f}% brightness")
            
        except Exception as e:
            logger.error(f"Failed to set LED color: {e}")
    
    async def set_led_hex(self, hex_color: str, brightness: float = 1.0):
        
        hex_color = hex_color.lstrip('#')
        
        if len(hex_color) != 6:
            raise ValueError("Invalid hex color format")
        
        try:
            red = int(hex_color[0:2], 16)
            green = int(hex_color[2:4], 16)
            blue = int(hex_color[4:6], 16)
            
            await self.set_led_color(red, green, blue, brightness)
            
        except ValueError as e:
            logger.error(f"Invalid hex color: {hex_color}")
            raise
    
    async def led_off(self):
        
        if not self.is_initialized:
            raise RuntimeError("Hardware controller not initialized")
        
        try:
            for pwm in self.led_pwm.values():
                pwm.ChangeDutyCycle(0)
            
            self.current_led_state = {
                'red': 0,
                'green': 0,
                'blue': 0,
                'brightness': 0.0,
                'is_on': False
            }
            
            logger.debug("LED turned off")
            
        except Exception as e:
            logger.error(f"Failed to turn off LED: {e}")
    
    async def get_led_status(self) -> dict:
        
        if not self.is_initialized:
            raise RuntimeError("Hardware controller not initialized")
        
        return self.current_led_state.copy()
    
    async def get_buzzer_status(self) -> dict:
        
        if not self.is_initialized:
            raise RuntimeError("Hardware controller not initialized")
        
        if (self.current_buzzer_state['is_active'] and 
            self.current_buzzer_state['start_time'] and 
            self.current_buzzer_state['duration']):
            
            elapsed_time = time.time() - self.current_buzzer_state['start_time']
            if elapsed_time >= self.current_buzzer_state['duration']:
                self.current_buzzer_state = {
                    'is_active': False,
                    'frequency': 0,
                    'start_time': None,
                    'duration': 0
                }
        
        return {
            'is_active': bool(self.current_buzzer_state['is_active']),
            'frequency': int(self.current_buzzer_state['frequency']),
            'start_time': self.current_buzzer_state['start_time'],
            'duration': float(self.current_buzzer_state['duration'])
        }
    
    async def led_fade(self, red: int, green: int, blue: int, 
                      fade_time: float = 1.0, steps: int = 50):
        
        step_time = fade_time / steps
        
        for i in range(steps + 1):
            progress = i / steps
            current_red = int(red * progress)
            current_green = int(green * progress)
            current_blue = int(blue * progress)
            
            await self.set_led_color(current_red, current_green, current_blue)
            await asyncio.sleep(step_time)
    
    async def play_buzzer_tone(self, frequency: int, duration: float = 0.5):
        
        if not self.is_initialized:
            raise RuntimeError("Hardware controller not initialized")
        
        try:
            self.current_buzzer_state = {
                'is_active': True,
                'frequency': frequency,
                'start_time': time.time(),
                'duration': duration
            }
            
            self.buzzer_pwm.ChangeFrequency(frequency)
            self.buzzer_pwm.ChangeDutyCycle(50)
            
            await asyncio.sleep(duration)
            
            self.buzzer_pwm.ChangeDutyCycle(0)
            
            self.current_buzzer_state = {
                'is_active': False,
                'frequency': 0,
                'start_time': None,
                'duration': 0
            }
            
            logger.debug(f"Buzzer played at {frequency}Hz for {duration}s")
            
        except Exception as e:
            logger.error(f"Failed to play buzzer tone: {e}")
            self.current_buzzer_state = {
                'is_active': False,
                'frequency': 0,
                'start_time': None,
                'duration': 0
            }
    
    async def play_buzzer_melody(self, notes: list):
        
        for frequency, duration in notes:
            await self.play_buzzer_tone(frequency, duration)
            await asyncio.sleep(0.1)
    
    async def buzzer_beep(self, count: int = 1, frequency: int = 1000, 
                         duration: float = 0.2, pause: float = 0.2):
        
        for i in range(count):
            await self.play_buzzer_tone(frequency, duration)
            if i < count - 1:
                await asyncio.sleep(pause)
    
    def cleanup(self):
        
        try:
            if self.is_initialized:
                for pwm in self.led_pwm.values():
                    pwm.stop()
                
                if self.buzzer_pwm:
                    self.buzzer_pwm.stop()
                
                GPIO.cleanup()
                
                self.is_initialized = False
                logger.info("Hardware controller cleaned up")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

class Colors:
    
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    WHITE = (255, 255, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    ORANGE = (255, 165, 0)
    PURPLE = (128, 0, 128)
    PINK = (255, 192, 203)
    OFF = (0, 0, 0)

class Notes:
    
    C4 = 262
    D4 = 294
    E4 = 330
    F4 = 349
    G4 = 392
    A4 = 440
    B4 = 494
    C5 = 523

"""
Hardware Controller Module
Handles RGB LED and passive buzzer control via GPIO
"""

import RPi.GPIO as GPIO
import time
import asyncio
import logging
from typing import Tuple, Optional
from config import GPIOConfig

logger = logging.getLogger(__name__)

class HardwareController:
    """Controls RGB LED and passive buzzer"""
    
    def __init__(self):
        """Initialize hardware controller"""
        self.is_initialized = False
        self.led_pwm = {}
        self.buzzer_pwm = None
        
    async def initialize(self) -> bool:
        """Initialize GPIO and hardware components"""
        try:
            # Set GPIO mode
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup RGB LED pins
            GPIO.setup(GPIOConfig.LED_RED_PIN, GPIO.OUT)
            GPIO.setup(GPIOConfig.LED_GREEN_PIN, GPIO.OUT)
            GPIO.setup(GPIOConfig.LED_BLUE_PIN, GPIO.OUT)
            
            # Setup buzzer pin
            GPIO.setup(GPIOConfig.BUZZER_PIN, GPIO.OUT)
            
            # Initialize PWM for RGB LED (1000 Hz frequency)
            self.led_pwm['red'] = GPIO.PWM(GPIOConfig.LED_RED_PIN, 1000)
            self.led_pwm['green'] = GPIO.PWM(GPIOConfig.LED_GREEN_PIN, 1000)
            self.led_pwm['blue'] = GPIO.PWM(GPIOConfig.LED_BLUE_PIN, 1000)
            
            # Start PWM with 0% duty cycle (LED off)
            for pwm in self.led_pwm.values():
                pwm.start(0)
            
            # Initialize PWM for buzzer
            self.buzzer_pwm = GPIO.PWM(GPIOConfig.BUZZER_PIN, 1000)
            self.buzzer_pwm.start(0)
            
            self.is_initialized = True
            logger.info("Hardware controller initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize hardware controller: {e}")
            return False
    
    async def set_led_color(self, red: int, green: int, blue: int, brightness: float = 1.0):
        """
        Set RGB LED color and brightness
        
        Args:
            red: Red value (0-255)
            green: Green value (0-255)
            blue: Blue value (0-255)
            brightness: Brightness multiplier (0.0-1.0)
        """
        if not self.is_initialized:
            raise RuntimeError("Hardware controller not initialized")
        
        try:
            # Clamp values to valid ranges
            red = max(0, min(255, red))
            green = max(0, min(255, green))
            blue = max(0, min(255, blue))
            brightness = max(0.0, min(1.0, brightness))
            
            # Convert to duty cycle (0-100%)
            red_duty = (red / 255.0) * brightness * 100
            green_duty = (green / 255.0) * brightness * 100
            blue_duty = (blue / 255.0) * brightness * 100
            
            # Apply PWM values
            self.led_pwm['red'].ChangeDutyCycle(red_duty)
            self.led_pwm['green'].ChangeDutyCycle(green_duty)
            self.led_pwm['blue'].ChangeDutyCycle(blue_duty)
            
            logger.debug(f"LED color set to RGB({red}, {green}, {blue}) at {brightness*100:.1f}% brightness")
            
        except Exception as e:
            logger.error(f"Failed to set LED color: {e}")
    
    async def set_led_hex(self, hex_color: str, brightness: float = 1.0):
        """
        Set RGB LED color using hex string
        
        Args:
            hex_color: Hex color string (e.g., "#FF0000" or "FF0000")
            brightness: Brightness multiplier (0.0-1.0)
        """
        # Remove # if present
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
        """Turn off RGB LED"""
        await self.set_led_color(0, 0, 0)
    
    async def led_fade(self, red: int, green: int, blue: int, 
                      fade_time: float = 1.0, steps: int = 50):
        """
        Fade LED to specified color
        
        Args:
            red: Target red value (0-255)
            green: Target green value (0-255)
            blue: Target blue value (0-255)
            fade_time: Time to complete fade (seconds)
            steps: Number of fade steps
        """
        step_time = fade_time / steps
        
        for i in range(steps + 1):
            progress = i / steps
            current_red = int(red * progress)
            current_green = int(green * progress)
            current_blue = int(blue * progress)
            
            await self.set_led_color(current_red, current_green, current_blue)
            await asyncio.sleep(step_time)
    
    async def play_buzzer_tone(self, frequency: int, duration: float = 0.5):
        """
        Play a tone on the passive buzzer
        
        Args:
            frequency: Frequency in Hz (100-5000)
            duration: Duration in seconds
        """
        if not self.is_initialized:
            raise RuntimeError("Hardware controller not initialized")
        
        try:
            # Clamp frequency to reasonable range
            frequency = max(100, min(5000, frequency))
            
            # Change PWM frequency and start
            self.buzzer_pwm.ChangeFrequency(frequency)
            self.buzzer_pwm.ChangeDutyCycle(50)  # 50% duty cycle for square wave
            
            logger.debug(f"Playing buzzer tone at {frequency}Hz for {duration}s")
            
            # Play for specified duration
            await asyncio.sleep(duration)
            
            # Stop buzzer
            self.buzzer_pwm.ChangeDutyCycle(0)
            
        except Exception as e:
            logger.error(f"Failed to play buzzer tone: {e}")
    
    async def play_buzzer_melody(self, notes: list):
        """
        Play a melody on the buzzer
        
        Args:
            notes: List of tuples (frequency, duration)
        """
        for frequency, duration in notes:
            await self.play_buzzer_tone(frequency, duration)
            await asyncio.sleep(0.1)  # Small pause between notes
    
    async def buzzer_beep(self, count: int = 1, frequency: int = 1000, 
                         duration: float = 0.2, pause: float = 0.2):
        """
        Make buzzer beep multiple times
        
        Args:
            count: Number of beeps
            frequency: Beep frequency in Hz
            duration: Duration of each beep
            pause: Pause between beeps
        """
        for i in range(count):
            await self.play_buzzer_tone(frequency, duration)
            if i < count - 1:  # Don't pause after last beep
                await asyncio.sleep(pause)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        try:
            if self.is_initialized:
                # Stop all PWM
                for pwm in self.led_pwm.values():
                    pwm.stop()
                
                if self.buzzer_pwm:
                    self.buzzer_pwm.stop()
                
                # Clean up GPIO
                GPIO.cleanup()
                
                self.is_initialized = False
                logger.info("Hardware controller cleaned up")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Common color presets
class Colors:
    """Common RGB color presets"""
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

# Common musical notes (frequencies in Hz)
class Notes:
    """Common musical note frequencies"""
    C4 = 262
    D4 = 294
    E4 = 330
    F4 = 349
    G4 = 392
    A4 = 440
    B4 = 494
    C5 = 523

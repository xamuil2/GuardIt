#!/usr/bin/env python3
"""
Arduino-Style Buzzer Test - Replicate Arduino tone() function
This should produce the same volume as your Arduino
"""

import RPi.GPIO as GPIO
import time

BUZZER_PIN = 21

class ArduinoBuzzer:
    """Replicate Arduino's tone() functionality for maximum volume"""
    
    def __init__(self, pin):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
    
    def tone(self, frequency, duration_ms):
        """
        Generate tone exactly like Arduino's tone() function
        Arduino tone() creates a 50% duty cycle square wave
        """
        if frequency <= 0:
            return
        
        period = 1.0 / frequency
        half_period = period / 2.0
        cycles = int((duration_ms / 1000.0) * frequency)
        
        print(f"🎵 Tone: {frequency}Hz for {duration_ms}ms ({cycles} cycles)")
        
        for _ in range(cycles):
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(half_period)
            GPIO.output(self.pin, GPIO.LOW)
            time.sleep(half_period)
    
    def no_tone(self):
        """Stop the tone - like Arduino's noTone()"""
        GPIO.output(self.pin, GPIO.LOW)
    
    def cleanup(self):
        """Cleanup GPIO"""
        self.no_tone()
        GPIO.cleanup()

def test_arduino_tones():
    """Test different frequencies like Arduino would generate"""
    print("🔊 Arduino-Style Buzzer Test")
    print("=" * 40)
    print("This replicates Arduino's tone() function exactly")
    print()
    
    buzzer = ArduinoBuzzer(BUZZER_PIN)
    
    try:
        # Test various frequencies (common Arduino buzzer frequencies)
        test_frequencies = [
            (262, 500, "C4 note"),      # Middle C
            (294, 500, "D4 note"),      # D
            (330, 500, "E4 note"),      # E
            (349, 500, "F4 note"),      # F
            (392, 500, "G4 note"),      # G
            (440, 500, "A4 note"),      # A (concert pitch)
            (494, 500, "B4 note"),      # B
            (523, 500, "C5 note"),      # High C
            (1000, 1000, "1kHz alert"), # Common alert tone
            (2000, 1000, "2kHz alert"), # High alert tone
            (500, 2000, "500Hz long"),  # Low frequency long
        ]
        
        for freq, duration, description in test_frequencies:
            print(f"Testing {description}: {freq}Hz for {duration}ms")
            buzzer.tone(freq, duration)
            time.sleep(0.3)  # Pause between tones
        
        print("\n🚨 Testing Alert Pattern (like GuardIt alerts):")
        
        # Test alert pattern - rapid beeps
        for i in range(5):
            print(f"Alert beep {i+1}/5")
            buzzer.tone(2000, 200)  # 200ms beep
            time.sleep(0.2)         # 200ms pause
        
        print("\n✅ Arduino-style buzzer test completed!")
        print("This should sound much louder and clearer than PWM")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
    finally:
        buzzer.cleanup()

def test_pwm_vs_digital():
    """Compare PWM vs digital toggle methods"""
    print("\n🔬 Comparing PWM vs Digital Toggle Methods")
    print("=" * 45)
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    try:
        print("\n1️⃣ Testing PWM method (current approach):")
        pwm = GPIO.PWM(BUZZER_PIN, 2000)
        pwm.start(50)
        time.sleep(2)
        pwm.stop()
        time.sleep(0.5)
        
        print("\n2️⃣ Testing Digital Toggle method (Arduino-style):")
        buzzer = ArduinoBuzzer(BUZZER_PIN)
        buzzer.tone(2000, 2000)  # 2 seconds at 2kHz
        
        print("\n🎯 Which was louder? The Digital Toggle should match Arduino volume!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    try:
        test_arduino_tones()
        test_pwm_vs_digital()
        
        print("\n💡 Key Findings:")
        print("   - Arduino uses digital toggle (HIGH/LOW) not PWM")
        print("   - This creates a perfect 50% duty cycle square wave")
        print("   - Should produce the same volume as your Arduino!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        GPIO.cleanup()

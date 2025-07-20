#!/usr/bin/env python3
"""
Buzzer Volume Test - Fix the quiet buzzer issue
Testing different PWM configurations to match Arduino volume
"""

import RPi.GPIO as GPIO
import time

BUZZER_PIN = 21

def test_buzzer_configurations():
    """Test different PWM configurations to find the loudest setup"""
    print("🔊 Testing Buzzer Volume Configurations")
    print("=" * 50)
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    # Test different frequencies and duty cycles
    test_configs = [
        (500, 50, "Low freq, 50% duty"),
        (1000, 50, "Medium freq, 50% duty"),
        (2000, 50, "High freq, 50% duty"),
        (2500, 50, "Very high freq, 50% duty"),
        (3000, 50, "Ultra high freq, 50% duty"),
        (1000, 25, "Medium freq, 25% duty"),
        (1000, 75, "Medium freq, 75% duty"),
        (1000, 90, "Medium freq, 90% duty"),
        (2000, 25, "High freq, 25% duty"),
        (2000, 75, "High freq, 75% duty"),
        (2000, 90, "High freq, 90% duty"),
    ]
    
    for freq, duty, description in test_configs:
        print(f"\n🎵 Testing: {description}")
        print(f"   Frequency: {freq}Hz, Duty Cycle: {duty}%")
        
        buzzer_pwm = GPIO.PWM(BUZZER_PIN, freq)
        buzzer_pwm.start(duty)
        
        time.sleep(2)  # Buzz for 2 seconds
        
        buzzer_pwm.stop()
        time.sleep(0.5)  # Pause between tests
    
    print("\n🔇 Testing on/off pattern (like Arduino digitalWrite)")
    # Test rapid on/off like Arduino's tone() function
    for i in range(1000):  # 1000 cycles at ~1kHz
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.0005)  # 0.5ms on
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(0.0005)  # 0.5ms off
    
    print("\n✅ Buzzer test completed")
    GPIO.cleanup()

def arduino_style_tone(frequency, duration_ms):
    """Generate tone similar to Arduino's tone() function"""
    print(f"🎵 Arduino-style tone: {frequency}Hz for {duration_ms}ms")
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    # Calculate period
    period = 1.0 / frequency
    half_period = period / 2.0
    
    # Calculate number of cycles
    cycles = int((duration_ms / 1000.0) * frequency)
    
    print(f"   Period: {period*1000:.2f}ms, Half-period: {half_period*1000:.2f}ms, Cycles: {cycles}")
    
    # Generate square wave manually
    for _ in range(cycles):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(half_period)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(half_period)
    
    GPIO.cleanup()

if __name__ == "__main__":
    print("🚀 Buzzer Volume Diagnostic Test")
    print("This will test different configurations to find the loudest setup")
    print("Press Ctrl+C to stop at any time\n")
    
    try:
        # Test PWM configurations
        test_buzzer_configurations()
        
        print("\n" + "="*50)
        print("🎯 Testing Arduino-style tones:")
        
        # Test Arduino-style tones
        arduino_style_tone(1000, 1000)  # 1kHz for 1 second
        time.sleep(0.5)
        arduino_style_tone(2000, 1000)  # 2kHz for 1 second
        time.sleep(0.5)
        arduino_style_tone(500, 1000)   # 500Hz for 1 second
        
        print("\n✅ All tests completed!")
        print("💡 The loudest configuration should be noted for the main script")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        GPIO.cleanup()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        GPIO.cleanup()

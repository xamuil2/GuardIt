#!/usr/bin/env python3
"""
Buzzer Duty Cycle Test - Test different PWM duty cycles for maximum volume
"""

import RPi.GPIO as GPIO
import time

BUZZER_PIN = 21

def test_duty_cycles():
    """Test different PWM duty cycles to find the loudest"""
    print("🔊 Testing PWM Duty Cycles for Maximum Volume")
    print("=" * 50)
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    frequency = 2000  # 2kHz like your Arduino
    
    # Test different duty cycles
    duty_cycles = [10, 25, 50, 75, 90, 95, 100]
    
    for duty in duty_cycles:
        print(f"\n🎵 Testing {duty}% duty cycle at {frequency}Hz")
        
        try:
            buzzer_pwm = GPIO.PWM(BUZZER_PIN, frequency)
            buzzer_pwm.start(duty)
            
            time.sleep(3)  # 3 seconds to hear the difference
            
            buzzer_pwm.stop()
            del buzzer_pwm  # Clean up PWM object
            
        except Exception as e:
            print(f"   Error with {duty}% duty cycle: {e}")
        
        time.sleep(0.5)  # Pause between tests
    
    print("\n🎯 Which duty cycle was loudest?")
    print("   Typically 100% should be loudest for passive buzzers")
    
    GPIO.cleanup()

def test_100_percent_extended():
    """Extended test of 100% duty cycle"""
    print("\n🔊 Extended 100% Duty Cycle Test")
    print("=" * 40)
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    frequencies = [500, 1000, 1500, 2000, 2500, 3000]
    
    for freq in frequencies:
        print(f"🎵 Testing {freq}Hz at 100% duty cycle")
        
        try:
            buzzer_pwm = GPIO.PWM(BUZZER_PIN, freq)
            buzzer_pwm.start(100)  # 100% duty cycle
            
            time.sleep(2)
            
            buzzer_pwm.stop()
            del buzzer_pwm
            
        except Exception as e:
            print(f"   Error: {e}")
        
        time.sleep(0.3)
    
    GPIO.cleanup()

def compare_pwm_vs_digital_100():
    """Compare 100% PWM vs digital toggle"""
    print("\n⚔️ PWM 100% vs Digital Toggle Comparison")
    print("=" * 45)
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    frequency = 2000
    
    print(f"1️⃣ PWM at 100% duty cycle, {frequency}Hz for 3 seconds:")
    try:
        buzzer_pwm = GPIO.PWM(BUZZER_PIN, frequency)
        buzzer_pwm.start(100)
        time.sleep(3)
        buzzer_pwm.stop()
        del buzzer_pwm
    except Exception as e:
        print(f"PWM error: {e}")
    
    time.sleep(1)
    
    print(f"2️⃣ Digital toggle (Arduino-style) at {frequency}Hz for 3 seconds:")
    period = 1.0 / frequency
    half_period = period / 2.0
    cycles = int(3.0 * frequency)  # 3 seconds worth
    
    for _ in range(cycles):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(half_period)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(half_period)
    
    print("\n🎯 Which method was louder?")
    
    GPIO.cleanup()

if __name__ == "__main__":
    print("🚀 Buzzer Maximum Volume Test")
    print("Testing to find the loudest configuration")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Test different duty cycles
        test_duty_cycles()
        
        # Extended 100% test
        test_100_percent_extended()
        
        # Direct comparison
        compare_pwm_vs_digital_100()
        
        print("\n✅ Volume tests completed!")
        print("💡 The loudest method should be used in the main script")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
        GPIO.cleanup()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        GPIO.cleanup()

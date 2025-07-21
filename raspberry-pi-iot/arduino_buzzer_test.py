import RPi.GPIO as GPIO
import time

BUZZER_PIN = 21

class ArduinoBuzzer:

    def __init__(self, pin):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
    
    def tone(self, frequency, duration_ms):
        
        if frequency <= 0:
            return
        
        period = 1.0 / frequency
        half_period = period / 2.0
        cycles = int((duration_ms / 1000.0) * frequency)

        for _ in range(cycles):
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(half_period)
            GPIO.output(self.pin, GPIO.LOW)
            time.sleep(half_period)
    
    def no_tone(self):
        
        GPIO.output(self.pin, GPIO.LOW)
    
    def cleanup(self):
        
        self.no_tone()
        GPIO.cleanup()

def test_arduino_tones():

    buzzer = ArduinoBuzzer(BUZZER_PIN)
    
    try:
        test_frequencies = [
            (262, 500, "C4 note"),
            (294, 500, "D4 note"),
            (330, 500, "E4 note"),
            (349, 500, "F4 note"),
            (392, 500, "G4 note"),
            (440, 500, "A4 note"),
            (494, 500, "B4 note"),
            (523, 500, "C5 note"),
            (1000, 1000, "1kHz alert"),
            (2000, 1000, "2kHz alert"),
            (500, 2000, "500Hz long"),
        ]
        
        for freq, duration, description in test_frequencies:
            buzzer.tone(freq, duration)
            time.sleep(0.3)

        for i in range(5):
            buzzer.tone(2000, 200)
            time.sleep(0.2)

    except KeyboardInterrupt:
    finally:
        buzzer.cleanup()

def test_pwm_vs_digital():

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    try:
        pwm = GPIO.PWM(BUZZER_PIN, 2000)
        pwm.start(50)
        time.sleep(2)
        pwm.stop()
        time.sleep(0.5)
        
        buzzer = ArduinoBuzzer(BUZZER_PIN)
        buzzer.tone(2000, 2000)

    except Exception as e:
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    try:
        test_arduino_tones()
        test_pwm_vs_digital()

    except Exception as e:
        GPIO.cleanup()

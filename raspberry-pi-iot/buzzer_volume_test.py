import RPi.GPIO as GPIO
import time

BUZZER_PIN = 21

def test_buzzer_configurations():

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
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
        
        buzzer_pwm = GPIO.PWM(BUZZER_PIN, freq)
        buzzer_pwm.start(duty)
        
        time.sleep(2)
        
        buzzer_pwm.stop()
        time.sleep(0.5)
    
    for i in range(1000):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.0005)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(0.0005)
    
    GPIO.cleanup()

def arduino_style_tone(frequency, duration_ms):

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    period = 1.0 / frequency
    half_period = period / 2.0
    
    cycles = int((duration_ms / 1000.0) * frequency)

    for _ in range(cycles):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(half_period)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(half_period)
    
    GPIO.cleanup()

if __name__ == "__main__":
    
    try:
        test_buzzer_configurations()

        arduino_style_tone(1000, 1000)
        time.sleep(0.5)
        arduino_style_tone(2000, 1000)
        time.sleep(0.5)
        arduino_style_tone(500, 1000)

    except KeyboardInterrupt:
        GPIO.cleanup()
    except Exception as e:
        GPIO.cleanup()

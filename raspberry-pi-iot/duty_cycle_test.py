import RPi.GPIO as GPIO
import time

BUZZER_PIN = 21

def test_duty_cycles():

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    frequency = 2000
    
    duty_cycles = [10, 25, 50, 75, 90, 95, 100]
    
    for duty in duty_cycles:
        
        try:
            buzzer_pwm = GPIO.PWM(BUZZER_PIN, frequency)
            buzzer_pwm.start(duty)
            
            time.sleep(3)
            
            buzzer_pwm.stop()
            del buzzer_pwm
            
        except Exception as e:
        
        time.sleep(0.5)

    GPIO.cleanup()

def test_100_percent_extended():

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    frequencies = [500, 1000, 1500, 2000, 2500, 3000]
    
    for freq in frequencies:
        
        try:
            buzzer_pwm = GPIO.PWM(BUZZER_PIN, freq)
            buzzer_pwm.start(100)
            
            time.sleep(2)
            
            buzzer_pwm.stop()
            del buzzer_pwm
            
        except Exception as e:
        
        time.sleep(0.3)
    
    GPIO.cleanup()

def compare_pwm_vs_digital_100():

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    
    frequency = 2000
    
    try:
        buzzer_pwm = GPIO.PWM(BUZZER_PIN, frequency)
        buzzer_pwm.start(100)
        time.sleep(3)
        buzzer_pwm.stop()
        del buzzer_pwm
    except Exception as e:
    
    time.sleep(1)
    
    period = 1.0 / frequency
    half_period = period / 2.0
    cycles = int(3.0 * frequency)
    
    for _ in range(cycles):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(half_period)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(half_period)

    GPIO.cleanup()

if __name__ == "__main__":
    
    try:
        test_duty_cycles()
        
        test_100_percent_extended()
        
        compare_pwm_vs_digital_100()

    except KeyboardInterrupt:
        GPIO.cleanup()
    except Exception as e:
        GPIO.cleanup()

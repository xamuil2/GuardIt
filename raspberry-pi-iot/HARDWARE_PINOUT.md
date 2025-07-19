# GuardIt Hardware Pinout and Wiring Guide

## 🔌 Raspberry Pi GPIO Pinout for GuardIt IoT Device

### 📍 Complete Pin Assignments

```
┌─────────┬──────┬──────────────────────────────────────┐
│ GPIO    │ Pin  │ Function                             │
├─────────┼──────┼──────────────────────────────────────┤
│ GPIO 2  │  3   │ I2C SDA (MPU9250/MPU6050)          │
│ GPIO 3  │  5   │ I2C SCL (MPU9250/MPU6050)          │
│ GPIO 18 │ 12   │ RGB LED - Red (PWM)                 │
│ GPIO 19 │ 35   │ RGB LED - Green (PWM)               │
│ GPIO 20 │ 38   │ RGB LED - Blue (PWM)                │
│ GPIO 21 │ 40   │ Passive Buzzer (PWM)                │
└─────────┴──────┴──────────────────────────────────────┘
```

### 🔧 Hardware Components Required

1. **MPU9250/MPU6050 IMU Sensor Module**
   - 9-axis (or 6-axis) motion sensor
   - I2C interface
   - 3.3V operation

2. **RGB LED (Common Cathode)**
   - 3 separate LEDs or RGB module
   - Forward voltage: ~2-3V each color
   - Current limiting resistors needed

3. **Passive Buzzer**
   - PWM-driven piezo buzzer
   - Operating voltage: 3-5V
   - Frequency range: 100Hz - 3kHz

4. **Resistors**
   - 220Ω - 470Ω for LED current limiting
   - Pull-up resistors (if needed for I2C)

### 🔌 Detailed Wiring Connections

#### **MPU9250/MPU6050 IMU Sensor**
```
IMU Module    │  Raspberry Pi
──────────────┼──────────────
VCC/3V3       │  Pin 1  (3.3V)
GND           │  Pin 6  (GND)
SDA           │  Pin 3  (GPIO 2 - I2C SDA)
SCL           │  Pin 5  (GPIO 3 - I2C SCL)
```

#### **RGB LED (Common Cathode)**
```
LED Color     │  Resistor  │  Raspberry Pi
──────────────┼────────────┼──────────────
Red Anode     │   220Ω     │  Pin 12 (GPIO 18)
Green Anode   │   220Ω     │  Pin 35 (GPIO 19)
Blue Anode    │   220Ω     │  Pin 38 (GPIO 20)
Common Cathode│     -      │  Pin 6  (GND)
```

#### **Passive Buzzer**
```
Buzzer        │  Raspberry Pi
──────────────┼──────────────
Positive (+)  │  Pin 40 (GPIO 21)
Negative (-)  │  Pin 6  (GND)
```

### 📋 Physical Layout Diagram

```
    Raspberry Pi 4B GPIO Header (Top View)
    ┌─────────────────────────────────────┐
    │ (1) 3V3    ●  ●  (2) 5V             │  ← Power for IMU
    │ (3) SDA    ●  ●  (4) 5V             │  ← I2C Data
    │ (5) SCL    ●  ●  (6) GND            │  ← I2C Clock & Ground
    │ (7) GPIO4  ●  ●  (8) GPIO14         │
    │ (9) GND    ●  ●  (10) GPIO15        │
    │(11) GPIO17 ●  ●  (12) GPIO18        │  ← Red LED
    │(13) GPIO27 ●  ●  (14) GND           │
    │(15) GPIO22 ●  ●  (16) GPIO23        │
    │(17) 3V3    ●  ●  (18) GPIO24        │
    │(19) GPIO10 ●  ●  (20) GND           │
    │(21) GPIO9  ●  ●  (22) GPIO25        │
    │(23) GPIO11 ●  ●  (24) GPIO8         │
    │(25) GND    ●  ●  (26) GPIO7         │
    │(27) GPIO0  ●  ●  (28) GPIO1         │
    │(29) GPIO5  ●  ●  (30) GND           │
    │(31) GPIO6  ●  ●  (32) GPIO12        │
    │(33) GPIO13 ●  ●  (34) GND           │
    │(35) GPIO19 ●  ●  (36) GPIO16        │  ← Green LED
    │(37) GPIO26 ●  ●  (38) GPIO20        │  ← Blue LED
    │(39) GND    ●  ●  (40) GPIO21        │  ← Buzzer
    └─────────────────────────────────────┘
```

### ⚡ Power Requirements

- **Raspberry Pi**: 5V, 2.5-3A power supply
- **IMU Sensor**: 3.3V (provided by Pi)
- **RGB LED**: 3.3V through GPIO with current limiting
- **Buzzer**: 3.3V through GPIO

### 🔧 Assembly Instructions

1. **Enable I2C on Raspberry Pi:**
   ```bash
   sudo raspi-config
   # Navigate to: Interfacing Options > I2C > Enable
   ```

2. **Wire IMU Sensor:**
   - Connect VCC to 3.3V (Pin 1)
   - Connect GND to Ground (Pin 6)
   - Connect SDA to GPIO 2 (Pin 3)
   - Connect SCL to GPIO 3 (Pin 5)

3. **Wire RGB LED:**
   - Red: GPIO 18 (Pin 12) → 220Ω resistor → Red LED anode
   - Green: GPIO 19 (Pin 35) → 220Ω resistor → Green LED anode
   - Blue: GPIO 20 (Pin 38) → 220Ω resistor → Blue LED anode
   - Connect all cathodes to Ground (Pin 6)

4. **Wire Buzzer:**
   - Positive to GPIO 21 (Pin 40)
   - Negative to Ground (Pin 6)

### 🧪 Testing Commands

After wiring, test your hardware:

```bash
# Test I2C device detection
sudo i2cdetect -y 1

# Run the hardware test script
cd /home/guardit/Documents/GuardIt/raspberry-pi-iot
python3 hardware_test.py
```

### 📊 Expected I2C Addresses

- **MPU6050**: 0x68 (default) or 0x69 (if AD0 high)
- **MPU9250**: 0x68 (default) or 0x69 (if AD0 high)

### ⚠️ Important Notes

1. **Current Limiting**: Always use resistors with LEDs to prevent damage
2. **Voltage Levels**: All components run at 3.3V logic levels
3. **I2C Pull-ups**: Most IMU modules have built-in pull-up resistors
4. **PWM Frequency**: Using 1kHz PWM for smooth LED dimming and buzzer tones
5. **Ground Connections**: Ensure all components share common ground

### 🔍 Troubleshooting

**IMU Not Detected:**
- Check I2C wiring (SDA/SCL)
- Verify power connections (3.3V/GND)
- Run: `sudo i2cdetect -y 1`

**LEDs Not Working:**
- Check resistor values (220-470Ω)
- Verify common cathode wiring
- Test individual GPIO pins

**Buzzer Silent:**
- Check polarity (+ to GPIO, - to GND)
- Verify it's a passive buzzer (needs PWM)
- Test with different frequencies

### 🎯 Arduino vs Raspberry Pi Comparison

| Feature | Arduino Code | Raspberry Pi Code |
|---------|--------------|-------------------|
| I2C | `Wire.begin()` | `smbus2.SMBus()` |
| PWM | `analogWrite()` | `GPIO.PWM()` |
| Delay | `delay()` | `time.sleep()` |
| Serial | `Serial.print()` | `logger.info()` |
| IMU Read | `Wire.requestFrom()` | `read_i2c_block_data()` |

This setup exactly mirrors your Arduino logic but optimized for Raspberry Pi!

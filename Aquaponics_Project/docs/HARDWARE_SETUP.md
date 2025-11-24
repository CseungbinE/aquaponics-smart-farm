# Aquaponics Smart Farm - Hardware Setup Guide

## Overview

This document provides detailed instructions for setting up the hardware components of the Aquaponics Smart Farm monitoring system.

## Hardware Requirements

### Arduino Implementation

**Main Board:**
- Arduino Mega 2560 (recommended) or Arduino Uno (limited)
- USB cable for programming
- External power supply (12V, 1A minimum)

**Sensors:**
- pH sensor module (analog 0-5V output)
- EC/TDS sensor module (analog 0-5V output)
- DS18B20 temperature sensor (1-Wire)
- Dissolved Oxygen sensor (analog 0-5V output)
- Water level float switch or capacitive sensor
- Turbidity sensor (analog 0-5V output)

**Accessories:**
- Breadboard or prototyping shield
- Jumper wires (male-to-male and male-to-female)
- Resistors: 4.7kΩ (for 1-Wire), various values for voltage dividers
- SD card module (optional, for data logging)
- RTC DS3231 module (optional, for timestamps)
- WiFi Shield ESP8266 (optional, for wireless communication)

### Raspberry Pi Implementation

**Main Board:**
- Raspberry Pi 4B or 5 (minimum 2GB RAM)
- microSD card (16GB minimum)
- Power supply (5V, 3A for Pi 4B; 5V, 5A for Pi 5)
- HDMI cable and display (for initial setup)
- Ethernet cable or WiFi antenna

**Sensors:**
- pH sensor (with analog output)
- EC/TDS sensor (with analog output)
- DS18B20 temperature sensor
- Dissolved Oxygen sensor
- Water level sensor
- Turbidity sensor

**Accessories:**
- ADC converter (ADS1115 for Raspberry Pi analog inputs)
- I2C cables
- GPIO extension board
- Cooling case with fan
- Optional: Relay module for pump/aeration control

## Pin Assignments

### Arduino Mega 2560

| Sensor | Pin | Type | Notes |
|--------|-----|------|-------|
| pH | A0 | Analog | Connected to ADC 0 |
| EC/TDS | A1 | Analog | Connected to ADC 1 |
| Temperature | 4 | Digital | 1-Wire protocol |
| DO | A2 | Analog | Connected to ADC 2 |
| Water Level | 17 | Digital | Digital input |
| Turbidity | A3 | Analog | Connected to ADC 3 |
| SD Chip Select | 53 | Digital | SPI protocol |
| RTC SDA | 20 | Digital | I2C SDA |
| RTC SCL | 21 | Digital | I2C SCL |

### Raspberry Pi GPIO

| Sensor | GPIO | Type | Notes |
|--------|------|------|-------|
| Temperature | 4 | Digital | 1-Wire protocol |
| Water Level | 17 | Digital | Digital input |
| Pump Control | 27 | Digital | GPIO output (optional) |
| Aeration Control | 22 | Digital | GPIO output (optional) |

**Analog Sensors (via ADS1115):**
- A0 → pH sensor
- A1 → EC/TDS sensor
- A2 → DO sensor
- A3 → Turbidity sensor

## Wiring Diagrams

### pH Sensor

```
pH Sensor Module:
- VCC → Arduino 5V
- GND → Arduino GND
- Signal (out) → Arduino A0
```

### EC/TDS Sensor

```
EC Sensor Module:
- VCC → Arduino 5V
- GND → Arduino GND
- Signal (out) → Arduino A1 (with 10kΩ pull-down resistor if needed)
```

### DS18B20 Temperature Sensor

```
DS18B20 (3-pin package):
- GND → Arduino GND
- DQ (data) → Arduino Pin 4
  └─ With 4.7kΩ pull-up resistor to VCC
- VCC → Arduino 5V (or 3.3V)
```

### Dissolved Oxygen Sensor

```
DO Sensor Module:
- VCC → Arduino 5V
- GND → Arduino GND
- Signal (out) → Arduino A2
```

### Water Level Float Switch

```
Float Switch:
- Terminal 1 → Arduino Pin 17
- Terminal 2 → Arduino GND
```

### Turbidity Sensor

```
Turbidity Sensor Module:
- VCC → Arduino 5V
- GND → Arduino GND
- Signal (out) → Arduino A3
```

### ADS1115 ADC (for Raspberry Pi)

```
I2C Connection:
- SDA → Raspberry Pi GPIO 2
- SCL → Raspberry Pi GPIO 3
- VCC → Raspberry Pi 3.3V
- GND → Raspberry Pi GND

Analog Input Connection (example for pH):
- A0 → pH sensor signal
```

## Assembly Steps

### Arduino Setup

1. **Prepare the breadboard:**
   - Mount Arduino Mega on breadboard or prototyping shield
   - Organize power rails (5V and GND)

2. **Install power:**
   - Connect external 12V power supply to Arduino VIN and GND
   - OR use USB power (limited to 500mA)

3. **Connect analog sensors (pH, EC, DO, Turbidity):**
   - Connect all VCC lines to 5V rail
   - Connect all GND lines to GND rail
   - Connect signal outputs to respective analog pins (A0-A3)

4. **Connect digital sensors:**
   - Connect DS18B20 with pull-up resistor
   - Connect water level float switch to GPIO 17
   - Connect RTC DS3231 via I2C (SDA/SCL)

5. **Install SD card module (optional):**
   - Connect SPI lines: MOSI, MISO, SCK, CS
   - CS connected to pin 53

6. **Program Arduino:**
   - Upload `main.ino` using Arduino IDE
   - Verify all sensors are reading correctly

### Raspberry Pi Setup

1. **Initial OS Setup:**
   ```bash
   # Write Raspbian to microSD card using Raspberry Pi Imager
   # Boot Raspberry Pi with keyboard, mouse, and HDMI display
   # Run initial configuration
   sudo raspi-config
   # Enable I2C, SPI, and 1-Wire
   ```

2. **Connect sensors:**
   - Mount Raspberry Pi in case
   - Install ADS1115 ADC converter on I2C bus
   - Connect temperature sensor to GPIO 4
   - Connect water level sensor to GPIO 17
   - Connect analog sensors to ADS1115 inputs

3. **Install software:**
   ```bash
   git clone <repository-url>
   cd aquaponics/raspberry_pi
   pip install -r requirements.txt
   python app/main.py
   ```

## Sensor Calibration

### pH Sensor

1. Prepare three calibration solutions:
   - pH 4.0 (acidic buffer)
   - pH 7.0 (neutral buffer)
   - pH 10.0 (alkaline buffer)

2. Place sensor in pH 4.0 solution
3. Wait for 30 seconds
4. Record the analog value
5. Repeat for pH 7.0 and 10.0

6. Use calibration values in configuration

### EC Sensor

1. Prepare two EC solutions:
   - 1000 μS/cm (low)
   - 10000 μS/cm (high)

2. Measure voltage output from sensor in each solution
3. Record values for linear calibration

### Water Level Sensor

1. Note sensor position when water is present
2. Set threshold accordingly
3. Test by adding/removing water

## Power Considerations

### Arduino Power Budget
- Arduino Mega: 500 mA (USB) or 2A (external)
- pH sensor: 5-10 mA
- EC sensor: 5-10 mA
- DS18B20: 1 mA
- DO sensor: 5-15 mA
- Turbidity: 3-5 mA
- **Total: ~40-55 mA (well within USB limit)**

### Raspberry Pi Power Budget
- Raspberry Pi 4: 600-800 mA
- ADS1115: <1 mA
- Sensors: ~40-50 mA
- **Total: ~700-900 mA (requires dedicated 5V supply)**

## Mounting Considerations

- **Sensor probes:** Mount in water-tight enclosures
- **Electronics:** Use weatherproof boxes with ventilation
- **pH sensor:** Protect from light; store in KCl solution when not in use
- **EC sensor:** Prevent salt buildup; rinse after use
- **DO sensor:** Keep membrane clean; check regularly
- **Temperature:** Mount away from direct sunlight

## Weatherproofing

1. **Sensor enclosures:**
   - Use waterproof IP67 or IP68 rated boxes
   - Apply silicone sealant to cable entry points
   - Use cable glands for all connections

2. **Electronics enclosure:**
   - Mounting inside greenhouse or shed
   - Adequate ventilation to prevent condensation
   - DIN rail for component organization

3. **Cables:**
   - Use UV-resistant cables
   - Proper grounding for electromagnetic interference (EMI)
   - Cable conduit for protection from moisture/pests

## Testing

### Sensor Function Test

```bash
# Arduino: Monitor serial output
# Should see readings like:
# Time(s), pH, EC, Temp, DO, Level, Turbidity

# Raspberry Pi: Run test
python -c "from app.sensors import SensorArray; s = SensorArray(); print(s.read_all())"
```

### Analog Reading Range

- Expected range: 0-1023 for Arduino analog pins
- Expected range: 0-32767 for ADS1115 (16-bit ADC)

### Digital Signal Test

- Float switch: Should toggle LOW/HIGH
- Temperature: Should read valid range (-10 to +85°C)

## Troubleshooting

See `TROUBLESHOOTING.md` for sensor-specific issues.

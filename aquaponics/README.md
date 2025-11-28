# Aquaponics Smart Farm Concentration Monitoring System

A comprehensive IoT solution for real-time water quality monitoring in aquaponics systems using Arduino and Raspberry Pi.

## Features

- **Multi-Sensor Support**: pH, EC/TDS, Temperature, Dissolved Oxygen, Water Level, Turbidity
- **Real-time Monitoring**: Web dashboard with live updates (2-5 second refresh)
- **Dual Platform Support**: Arduino Mega 2560/Uno + Raspberry Pi 4B/5
- **Intelligent Alerting**: Configurable thresholds with WARNING/CRITICAL levels
- **Calibration Management**: Guided calibration routines with validation
- **Data Logging**: Local SQLite database with CSV/JSON export
- **Offline Capable**: Fully functional without internet connection
- **API-First Design**: RESTful endpoints for integration

## Quick Start

### Prerequisites

- **Arduino**: Arduino IDE 1.8.19+, Arduino Mega 2560 or Uno
- **Raspberry Pi**: Python 3.9+, Raspbian OS
- **Common**: All sensor hardware and wiring components

### Arduino Setup

```bash
cd arduino/
# Upload sketches using Arduino IDE
# 1. Open main.ino in Arduino IDE
# 2. Select board: Tools > Board > Arduino Mega 2560
# 3. Select port: Tools > Port > /dev/ttyUSB0
# 4. Click Upload
```

### Raspberry Pi Setup

```bash
cd raspberry_pi/
pip install -r requirements.txt
python app/main.py
```

Access the dashboard at: `http://localhost:5000`

## Architecture

```
aquaponics/
├── config.json             # System Configuration (Hardware, Thresholds, Database)
├── arduino/                # Arduino implementation (C++)
│   ├── main.ino            # Main sketch
│   ├── sensors.h           # Sensor interface definitions
│   ├── config.h            # Hardware configuration
│   └── libraries/          # Third-party libraries
├── raspberry_pi/           # Raspberry Pi implementation (Python)
│   ├── requirements.txt    # Python dependencies
│   └── app/
│       ├── main.py         # Application entry point
│       ├── sensors.py      # Sensor classes (Serial communication)
│       ├── database.py     # SQLite management
│       ├── api.py          # Flask API endpoints
│       ├── alerts.py       # Alert logic
│       ├── config.py       # Config loader
│       └── dashboard.py    # Web dashboard view
├── docs/                   # Documentation
├── specs/                  # Specifications and data models
└── docker-compose.yml      # Docker deployment
```

## Sensor Specifications

| Sensor | Type | Range | Resolution | Calibration |
|--------|------|-------|-----------|------------|
| pH | Analog | 0-14 | ±0.1 | 3-point (4.0, 7.0, 10.0) |
| EC/TDS | Analog | 0-2000 μS/cm | ±10 μS/cm | 2-point (1000, 10000) |
| Temperature | Digital (DS18B20) | -10 to +85°C | ±0.5°C | Factory calibrated |
| DO | Analog/Digital | 0-20 mg/L | ±0.1 mg/L | 2-point (0%, 100%) |
| Water Level | Analog | 0-100% | ±1% | Continuous (Depth based) |
| Turbidity | Analog | 0-1000 NTU | ±10 NTU | 1-point (clear water) |

## Aquaponics Water Quality Targets

| Parameter | Optimal Range | Unit | Warning | Critical |
|-----------|---------------|------|---------|----------|
| pH | 6.8-7.0 | - | 6.5-7.5 | <6.0 or >8.0 |
| EC | 1200-1600 | μS/cm | 1000-1800 | <800 or >2000 |
| Temperature | 20-26 | °C | 18-28 | <15 or >32 |
| DO | 5-8 | mg/L | >4 | <3 |
| Water Level | 80-100 | % | <60 | <40 |

## API Endpoints

```
GET  /api/current              # Current sensor readings
GET  /api/history?days=7       # Historical data
POST /api/alert                # Manual alert trigger
POST /api/calibration          # Calibration data submission
GET  /api/config               # Current configuration
POST /api/config               # Update configuration
GET  /api/export?format=csv    # Data export (CSV/JSON)
```

## Configuration

Edit `config.json` to customize:

```json
{
  "hardware": {
    "platform": "arduino",
    "sensors": {
      "pH": { "pin": "A0", "enabled": true },
      "EC": { "pin": "A1", "enabled": true },
      "temperature": { "pin": "4", "enabled": true },
      "DO": { "pin": "A2", "enabled": true },
      "water_level": { "pin": "A4", "enabled": true },
      "turbidity": { "pin": "A3", "enabled": true }
    }
  },
  "monitoring": {
    "reading_interval_seconds": 300,
    "averaging_window": 10,
    "alert_thresholds": {
      "pH": { "min": 5.5, "max": 7.5, "critical_min": 5.0, "critical_max": 8.0 },
      "EC": { "min": 1200, "max": 1600, "critical_min": 1000, "critical_max": 1800 },
      "temperature": { "min": 18, "max": 28, "critical_min": 15, "critical_max": 32 },
      "DO": { "min": 5, "critical_min": 3 },
      "water_level": { "min": 60, "critical_min": 40 },
      "turbidity": { "max": 500, "critical_max": 1000 }
    }
  },
  "database": {
    "type": "sqlite",
    "path": "./data/aquaponics.db",
    "backup_path": "./data/backups/"
  }
}
```

## Calibration Procedures

### pH Sensor (3-point)
1. Prepare 3 calibration solutions: pH 4.0, 7.0, 10.0
2. Run calibration routine via web dashboard
3. Follow on-screen prompts for each point
4. Validation takes ~30 seconds per point

### EC Sensor (2-point)
1. Prepare EC solutions: 1000 μS/cm, 10000 μS/cm
2. Run calibration via dashboard
3. Temperature compensation applied automatically

### DO Sensor (2-point)
1. Zero point: Nitrogen gas or distilled water reading
2. Span point: Air-saturated water at current temperature
3. Automatic temperature and altitude compensation

## Testing

```bash
# Run all tests
cd raspberry_pi/
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_sensors.py::TestPHSensor -v

# Generate coverage report
python -m pytest tests/ --cov=app --cov-report=html
```

## Docker Deployment (Raspberry Pi)

```bash
docker-compose up -d
# Dashboard available at http://localhost:5000
```

## Troubleshooting

### Common Issues

**Arduino not uploading:**
- Check USB cable connection
- Verify correct board selection in Arduino IDE
- Try different USB port
- Reset board: Press RST button while uploading

**Sensor readings erratic:**
- Verify wiring (check pin assignments in config.h)
- Check sensor is properly calibrated
- Verify analog reference voltage (5V or 3.3V)
- Ensure adequate power supply

**Dashboard not loading:**
- Verify Flask is running: `ps aux | grep flask`
- Check port 5000 is not in use: `sudo lsof -i :5000`
- Check for errors in logs: `tail -f app/logs/app.log`

**Database errors:**
- Delete corrupted database: `rm data/aquaponics.db`
- Re-run migrations: `python app/database.py --init`

## Hardware Wiring

See `docs/HARDWARE_SETUP.md` for detailed pin assignments and schematics.

## Documentation

- [Hardware Setup Guide](docs/HARDWARE_SETUP.md)
- [Installation Manual](docs/INSTALLATION.md)
- [Calibration Procedures](docs/CALIBRATION.md)
- [API Documentation](docs/API.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [Architecture Documentation](docs/ARCHITECTURE.md)

## License

MIT License - See LICENSE file for details

## Support

For issues, feature requests, or contributions, please open an issue on GitHub.

---

**Last Updated**: 2025-11-13
**Version**: 1.0.0
**Status**: Initial Implementation

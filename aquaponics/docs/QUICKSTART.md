# Aquaponics Smart Farm - Quick Start Guide

Get the Aquaponics Smart Farm monitoring system up and running in 5 minutes!

## 5-Minute Setup (Raspberry Pi)

### Prerequisites
- Raspberry Pi 4B or 5
- All sensors connected and powered
- Network connectivity (Ethernet or WiFi)
- Terminal access

### Quick Setup

```bash
# 1. Clone project
git clone <repository-url>
cd aquaponics/raspberry_pi

# 2. Install dependencies (1-2 minutes)
python3 -m venv ~/aquaponics-env
source ~/aquaponics-env/bin/activate
pip install -r requirements.txt

# 3. Start application (< 10 seconds)
python app/main.py

# 4. Open dashboard
# In browser: http://<pi-ip>:5000
```

**That's it!** Your dashboard is now running.

---

## First Steps

### 1. Check Sensor Readings

```
Dashboard: http://<pi-ip>:5000
```

Look for:
- All 6 sensors showing values
- Green status indicators (OK)
- Real-time graph updates

### 2. Verify Data Collection

```bash
# Check current readings
curl http://localhost:5000/api/current | python -m json.tool

# View recent data
sqlite3 data/aquaponics.db \
  "SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 5;"
```

### 3. Initial Calibration (Optional but Recommended)

For best accuracy, calibrate pH and EC sensors:

1. Open dashboard
2. Settings → Calibration
3. Follow on-screen instructions

See `CALIBRATION.md` for detailed procedures.

### 4. Set Alert Thresholds

Edit `../config.json` to match your system:

```json
"alert_thresholds": {
  "pH": { "min": 6.5, "max": 7.5 },
  "EC": { "min": 1000, "max": 2000 },
  "temperature": { "min": 18, "max": 28 }
}
```

---

## Common Tasks

### View Dashboard

```
http://<raspberry-pi-ip>:5000
```

### Get Sensor Data (API)

```bash
# Current readings
curl http://localhost:5000/api/current

# Last 7 days
curl http://localhost:5000/api/history?days=7

# Get statistics
curl http://localhost:5000/api/statistics?hours=24
```

### Export Data

```bash
# As JSON
curl http://localhost:5000/api/export?format=json&hours=24

# As CSV
curl http://localhost:5000/api/export?format=csv&hours=24
```

### Stop Application

```bash
# Press Ctrl+C to stop

# Or if running in background
pkill -f "python app/main.py"
```

### View Logs

```bash
# Real-time logs
tail -f logs/aquaponics.log

# Last 50 lines
tail -50 logs/aquaponics.log

# Search for errors
grep ERROR logs/aquaponics.log
```

---

## Docker Quick Start

```bash
# Ensure you are in the project root
cd ..  # If you were in raspberry_pi/ directory

# Build image
docker build -t aquaponics:latest .

# Run container
docker-compose up -d

# View logs
docker-compose logs -f aquaponics

# Stop container
docker-compose down
```

---

## Arduino Setup (5 minutes)

### Prerequisites
- Arduino Mega 2560
- All sensors connected
- Arduino IDE installed

### Upload Sketch

1. Open `arduino/main.ino` in Arduino IDE
2. Select board: **Tools → Board → Arduino Mega 2560**
3. Select port: **Tools → Port → /dev/ttyUSB0** (or your port)
4. Click **Upload** (or Ctrl+U)

### Verify Operation

1. Open **Serial Monitor** (Ctrl+Shift+M)
2. Set baud rate to **115200**
3. Should see sensor readings like:
   ```
   pH: 6.8, EC: 1350, Temp: 24.5, ...
   ```

---

## Troubleshooting

### Dashboard won't load
```bash
# Check if running
ps aux | grep python

# Start application
python app/main.py

# Check port
sudo lsof -i :5000
```

### No sensor readings
```bash
# Check if sensors are enabled in config.json
nano ../config.json

# View sensor status
curl http://localhost:5000/api/current
```

### Application crashes
```bash
# Check logs for errors
tail logs/aquaponics.log

# Run with debug mode
# Edit config.json: set "level": "DEBUG"
```

See `TROUBLESHOOTING.md` for more help.

---

## Next Steps

1. **Read Full Documentation**
   - `INSTALLATION.md` - Detailed installation
   - `HARDWARE_SETUP.md` - Pin assignments and wiring
   - `CALIBRATION.md` - Sensor calibration procedures
   - `API.md` - API endpoint reference

2. **Optimize Setup**
   - Calibrate sensors
   - Adjust alert thresholds
   - Configure backups
   - Setup auto-start (optional)

3. **Integrate with External Systems**
   - Push data to cloud (Firebase, AWS)
   - Send alerts via email/Slack
   - Log to external databases
   - Create custom dashboards

---

## API Quick Reference

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `/health` | System status | `curl http://localhost:5000/health` |
| `/api/current` | Latest readings | `curl http://localhost:5000/api/current` |
| `/api/history` | Historical data | `curl http://localhost:5000/api/history?days=7` |
| `/api/alerts/active` | Active alerts | `curl http://localhost:5000/api/alerts/active` |
| `/api/export` | Export data | `curl http://localhost:5000/api/export?format=json` |

---

## Keyboard Shortcuts

| Command | Description |
|---------|-------------|
| `Ctrl+C` | Stop application |
| `Ctrl+Shift+M` | Serial Monitor (Arduino IDE) |
| `Ctrl+U` | Upload sketch (Arduino IDE) |
| `tail -f logs/aquaponics.log` | Follow logs |
| `nano config.json` | Edit configuration |

---

## System Requirements

### Minimum
- Raspberry Pi 4B (2GB RAM)
- 16GB microSD card
- 5V 3A power supply
- Ethernet or WiFi
- 6 sensors

### Recommended
- Raspberry Pi 4B (4GB RAM) or Pi 5
- 32GB microSD card
- 5V 5A power supply
- Ethernet connection
- UPS/Battery backup

---

## File Structure

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

---

## Support & Resources

- **Documentation:** See `docs/` directory
- **Issues:** Check `TROUBLESHOOTING.md`
- **Configuration:** Edit `config.json`
- **Logs:** Check `logs/aquaponics.log`
- **API:** Reference `docs/API.md`

---

## Tips & Tricks

### Monitor Real-Time
```bash
watch -n 5 curl http://localhost:5000/api/current
```

### Backup Data
```bash
cp data/aquaponics.db data/aquaponics_$(date +%Y%m%d_%H%M%S).db
```

### Export Weekly Data
```bash
curl "http://localhost:5000/api/export?format=csv&hours=168" \
  -o export_$(date +%Y%m%d).csv
```

### Check System Health
```bash
# CPU/Memory
top

# Disk space
df -h

# Network
ifconfig

# Processes
ps aux | grep python
```

---

## Customization Examples

### Change Reading Interval
```json
"monitoring": {
  "reading_interval_seconds": 600  # 10 minutes instead of 5
}
```

### Increase Averaging
```json
"monitoring": {
  "averaging_window": 20  # More stable readings
}
```

### Custom Alert Thresholds
```json
"alert_thresholds": {
  "pH": {
    "min": 6.8,           # Warning if < 6.8
    "max": 7.0,           # Warning if > 7.0
    "critical_min": 6.5,  # Critical if < 6.5
    "critical_max": 7.5   # Critical if > 7.5
  }
}
```

---

**Happy Monitoring! 🌊**

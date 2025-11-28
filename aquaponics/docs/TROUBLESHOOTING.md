# Aquaponics Smart Farm - Troubleshooting Guide

## Quick Diagnostics

### System Health Check

```bash
# Check if system is running
curl http://localhost:5000/health

# Check current readings
curl http://localhost:5000/api/current

# Check for active alerts
curl http://localhost:5000/api/alerts/active

# View recent logs
tail -f logs/aquaponics.log

# Check database integrity
sqlite3 data/aquaponics.db ".tables"
```

---

## Common Issues and Solutions

### 1. Dashboard Not Loading

**Symptom:** Cannot access web interface at `http://localhost:5000`

**Possible Causes:**
- Application not running
- Port already in use
- Network connectivity issue
- Firewall blocking port

**Solutions:**

```bash
# Check if application is running
ps aux | grep python | grep main.py

# If not running, start it
python app/main.py

# Check if port 5000 is in use
sudo lsof -i :5000

# If in use, change port in config.json
# Or kill the process
sudo kill <PID>

# Test network connectivity
ping localhost
curl http://127.0.0.1:5000/health

# From another machine
ping <raspberry-pi-ip>
curl http://<raspberry-pi-ip>:5000/health
```

---

### 2. No Sensor Readings

**Symptom:** Dashboard shows empty or zero readings

**Possible Causes:**
- Sensors not connected
- Sensor readings are disabled in config
- Hardware/wiring issue
- Sensor failure

**Solutions:**

```bash
# Check if sensors are enabled
nano config.json
# Look for "enabled": true under each sensor

# Check sensor health
curl http://localhost:5000/api/current | python -m json.tool

# Look for "is_healthy": true/false for each sensor

# Test individual sensor (Arduino)
# Open Serial Monitor and verify readings
# Or check logs for sensor errors
grep -i "sensor\|error" logs/aquaponics.log

# Check wiring
# Verify pin assignments match config.h (Arduino) or config.json (Pi)
# Use multimeter to check voltage on sensor outputs
```

---

### 3. Sensor Readings Fluctuating Wildly

**Symptom:** Values jump erratically, not smooth

**Possible Causes:**
- Electrical noise/interference
- Loose wiring
- Sensor not calibrated
- Power supply instability
- Averaging window too small

**Solutions:**

```bash
# Increase averaging window in config.json
"averaging_window": 20  # Default is 10

# Check for electrical noise
# Move cables away from power supplies
# Use shielded cables for analog sensors
# Check ground connections

# Verify power supply
# Use multimeter to check voltage stability
# Recommended: 5.0V ±0.2V for sensors

# Recalibrate sensors
# See CALIBRATION.md for procedures

# Check data validity
sqlite3 data/aquaponics.db \
  "SELECT timestamp, pH, EC FROM sensor_readings ORDER BY timestamp DESC LIMIT 5;"
```

---

### 4. Sensor Timeout Errors

**Symptom:** Log shows "Sensor timeout" or "SENSOR_TIMEOUT" flags

**Possible Causes:**
- Arduino disconnected from Raspberry Pi
- USB cable fault
- Arduino sketch not running (or stuck)
- Sensor disconnected from Arduino

**Solutions:**

```bash
# 1. Check USB Connection
ls /dev/ttyUSB* /dev/ttyACM*
# Should list /dev/ttyUSB0 or similar

# 2. Check Permissions
ls -l /dev/ttyUSB0
# User should have read/write access (usually 'dialout' group)

# 3. Test Serial Communication
# Install minicom if needed: sudo apt install minicom
minicom -D /dev/ttyUSB0 -b 115200
# Should see JSON data stream: {"timestamp":..., "pH":...}

# 4. Check Arduino Hardware
# Verify sensors are connected to Arduino pins as per config.h
# Check Arduino power LED is on
```

---

### 5. Database Errors

**Symptom:** "database is locked" or "disk I/O error"

**Possible Causes:**
- Multiple processes accessing database
- Corrupted database file
- Disk full
- Insufficient permissions

**Solutions:**

```bash
# Check disk space
df -h
# Should have >100MB free

# Check for locked database
lsof | grep aquaponics.db

# Stop application
sudo systemctl stop aquaponics.service
# Or kill the process
ps aux | grep main.py
kill <PID>

# Remove lock files
rm data/aquaponics.db-wal
rm data/aquaponics.db-shm

# Verify database integrity
sqlite3 data/aquaponics.db "PRAGMA integrity_check;"

# If corrupted, backup and reset
cp data/aquaponics.db data/aquaponics.db.backup
rm data/aquaponics.db

# Restart application
python app/main.py

# Check permissions
ls -la data/
# Should be writable by current user
chmod 755 data/
```

---

### 6. API Errors (500 Internal Server Error)

**Symptom:** API endpoints return error 500

**Possible Causes:**
- Database connection error
- Invalid configuration
- Unhandled exception
- Out of memory

**Solutions:**

```bash
# Check logs for detailed error
tail -n 50 logs/aquaponics.log | grep ERROR

# Verify configuration is valid JSON
python -m json.tool config.json

# Check database connectivity
python -c "from app.database import DatabaseManager; db = DatabaseManager(); print(db.get_latest_reading())"

# Test individual components (Serial Manager)
python -c "from app.config import Config; from app.sensors import SerialSensorManager; conf = Config(); s = SerialSensorManager(conf); print(s.read_all())"

# Check memory usage
free -h
# If low, restart application

# Increase log verbosity
# Set "level": "DEBUG" in config.json
# Restart and check logs
```

---

### 7. Calibration Issues

**Symptom:** Calibration not working or readings still incorrect after calibration

**Possible Causes:**
- Calibration solutions expired
- Sensor contaminated
- Calibration not properly saved
- Wrong calibration procedure

**Solutions:**

```bash
# Verify calibration was saved
curl http://localhost:5000/api/calibration/pH | python -m json.tool

# Check calibration timestamps
sqlite3 data/aquaponics.db \
  "SELECT sensor_name, timestamp FROM calibrations ORDER BY timestamp DESC LIMIT 5;"

# Redo calibration
# Use fresh calibration solutions
# Follow procedures in CALIBRATION.md exactly
# Wait for full stabilization time

# For pH specifically
# Ensure sensor tip is not dried out
# Store in KCl solution between uses
# Replace if readings are more than ±0.5 pH off
```

---

### 8. High Alert Threshold

**Symptom:** System constantly triggering false alerts

**Possible Causes:**
- Thresholds set too tight
- Sensor readings are truly out of range
- Calibration issue
- Water quality actually poor

**Solutions:**

```bash
# Review recent readings
curl http://localhost:5000/api/statistics?hours=24 | python -m json.tool

# Check current thresholds
curl http://localhost:5000/api/config | python -m json.tool | grep -A 20 alert_thresholds

# Update thresholds if appropriate
# Edit config.json
# Or use API:
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"thresholds": {"pH": {"min": 6.5, "max": 7.5}}}'

# Check if calibration is needed
# Compare readings with manual tests

# Monitor for patterns in alerts
sqlite3 data/aquaponics.db \
  "SELECT timestamp, sensor_name, alert_type, value FROM alerts ORDER BY timestamp DESC LIMIT 20;"
```

---

### 9. Performance Issues

**Symptom:** Dashboard slow, API responses delayed, high CPU usage

**Possible Causes:**
- Too much data in database
- Insufficient system resources
- Network congestion
- Inefficient queries

**Solutions:**

```bash
# Check system resources
top
free -h
df -h

# Monitor network
iftop
# or
iperf3  # if network is suspected

# Check database size
du -sh data/aquaponics.db

# Clean old data
python -c "from app.database import DatabaseManager; db = DatabaseManager(); db.cleanup_old_data(retention_days=90)"

# Reduce update frequency
# Edit config.json: increase reading_interval_seconds
"reading_interval_seconds": 600  # 10 minutes instead of 5

# Optimize database
sqlite3 data/aquaponics.db "VACUUM;"
sqlite3 data/aquaponics.db "ANALYZE;"

# Check for stuck processes
ps aux | grep python
# Kill zombies if necessary

# Restart application
sudo systemctl restart aquaponics.service
```

---

### 10. Network Connectivity Issues

**Symptom:** Cannot access dashboard from another device

**Possible Causes:**
- Raspberry Pi not connected to network
- IP address incorrect
- Firewall blocking port
- WiFi issues

**Solutions:**

```bash
# Check network status
ip addr show
# or
ifconfig

# Test connectivity to Pi
ping <pi-ip>

# Check if port is open
telnet <pi-ip> 5000
# or
sudo nmap -p 5000 <pi-ip>

# Restart network
sudo systemctl restart networking

# For WiFi issues
sudo nmcli device show wlan0
sudo nmcli con up <SSID>

# Check firewall
sudo ufw status
sudo ufw allow 5000/tcp  # If needed

# Check application binding
sudo netstat -tlnp | grep 5000
# Should show listening on 0.0.0.0:5000
```

---

## Advanced Diagnostics

### Enable Debug Logging

```bash
# Edit config.json
"logging": {
  "level": "DEBUG"
}

# Restart application
# Now get detailed log messages
```

### Test Sensor Hardware Directly

**Arduino (via Serial Monitor):**
1. Connect Arduino to PC
2. Open Serial Monitor (Baud 115200)
3. Check if JSON data stream appears
4. Send command `STATUS` to check sensor health

**Raspberry Pi (via Terminal):**
```bash
# Read raw serial data directly from Python
python3 -c "
import serial
import time

try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    time.sleep(2) # Wait for connection
    if ser.in_waiting > 0:
        print(ser.readline().decode('utf-8').strip())
    else:
        print('No data waiting...')
    ser.close()
except Exception as e:
    print(f'Error: {e}')
"
```

### Monitor Sensor Data in Real-Time

```bash
# Watch sensor updates as they arrive
watch -n 5 'curl -s http://localhost:5000/api/current | python -m json.tool'

# Or tail the logs
tail -f logs/aquaponics.log | grep -i sensor
```

### Database Query Examples

```bash
# Get all readings from last 24 hours
sqlite3 data/aquaponics.db \
  "SELECT timestamp, pH, EC, temperature FROM sensor_readings WHERE timestamp > datetime('now', '-1 day') ORDER BY timestamp DESC;"

# Get critical alerts
sqlite3 data/aquaponics.db \
  "SELECT timestamp, sensor_name, message FROM alerts WHERE alert_type='CRITICAL' ORDER BY timestamp DESC LIMIT 10;"

# Get calibration history
sqlite3 data/aquaponics.db \
  "SELECT timestamp, sensor_name, calibration_type FROM calibrations ORDER BY timestamp DESC LIMIT 10;"
```

---

## Performance Metrics

### Expected System Performance

| Metric | Expected Value | Warning Level | Critical Level |
|--------|---|---|---|
| CPU Usage | <30% | >70% | >90% |
| Memory Usage | <50% | >80% | >95% |
| Disk Usage | <70% | >85% | >95% |
| API Response Time | <100ms | >500ms | >2s |
| Sensor Read Rate | 100% | <80% | <60% |
| Database Size | <1GB (90 days) | >5GB | >10GB |

---

## Getting Help

If problems persist:

1. **Collect diagnostic data:**
   ```bash
   mkdir aquaponics_diagnostic
   cp logs/aquaponics.log aquaponics_diagnostic/
   curl http://localhost:5000/api/current > aquaponics_diagnostic/current_readings.json
   sqlite3 data/aquaponics.db ".dump" > aquaponics_diagnostic/database_dump.sql
   dmesg | tail -50 > aquaponics_diagnostic/system_log.txt
   uname -a > aquaponics_diagnostic/system_info.txt
   ```

2. **Check documentation:**
   - Review relevant sections in other docs
   - Check `CALIBRATION.md` for sensor-specific procedures
   - Review `HARDWARE_SETUP.md` for wiring

3. **Consult logs:**
   - `logs/aquaponics.log` - Application logs
   - `journalctl` - System logs (if using systemd)
   - `/var/log/syslog` - System messages

4. **Test in isolation:**
   - Test sensors independently
   - Test API endpoints with curl
   - Test database queries directly

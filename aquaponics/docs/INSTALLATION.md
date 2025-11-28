# Aquaponics Smart Farm - Installation Guide

## System Requirements

### For Raspberry Pi (Recommended)
- Raspberry Pi 4B or 5
- 2GB RAM minimum (4GB recommended)
- 16GB microSD card minimum
- 5V 3A power supply (Pi 4) or 5V 5A (Pi 5)
- Ethernet or WiFi connectivity
- Linux-based OS (Raspbian/Raspberry Pi OS)

### For Arduino
- Arduino Mega 2560 or Uno
- External power supply (12V, 1A minimum)
- USB cable for programming
- All required sensors (see Hardware Setup Guide)

### For Development/Testing
- Python 3.9+
- pip (Python package manager)
- git (version control)

---

## Raspberry Pi Setup

### Step 1: Prepare Operating System

```bash
# Download and install Raspberry Pi OS
# Use Raspberry Pi Imager: https://www.raspberrypi.com/software/

# After first boot, update system
sudo apt update
sudo apt upgrade -y

# Enable required interfaces
sudo raspi-config
# → Interface Options
# → Enable I2C
# → Enable SPI
# → Enable 1-Wire
# → Reboot
```

### Step 2: Install Python Dependencies

```bash
# Install Python development tools
sudo apt install -y python3-dev python3-pip python3-venv

# Create virtual environment (recommended)
python3 -m venv ~/aquaponics-env
source ~/aquaponics-env/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Clone Project

```bash
# Clone repository
git clone <repository-url>
cd aquaponics/raspberry_pi

# Install Python dependencies
pip install -r requirements.txt
```

### Step 4: Configure Application

```bash
# Edit configuration
cp ../config.json .
nano config.json

# Key settings to update:
# - hardware.platform: "raspberry_pi"
# - hardware.sensors: Enable/disable as needed
# - web_server.host: "0.0.0.0" for remote access
# - web_server.port: 5000 (or other port)
```

### Step 5: Test Installation

```bash
# Run unit tests
cd tests
python -m pytest test_sensors.py -v

# Run database tests
python -m pytest test_database.py -v

# Run API tests
python -m pytest test_api.py -v
```

### Step 6: Start Application

```bash
# Run in foreground (for testing)
cd app
python main.py

# Or run in background
nohup python main.py > aquaponics.log 2>&1 &

# Access dashboard
# Open browser: http://<raspberry-pi-ip>:5000
```

### Step 7: Setup Auto-Start (Optional)

Create systemd service:

```bash
# Create service file
sudo nano /etc/systemd/system/aquaponics.service
```

Add content:
```ini
[Unit]
Description=Aquaponics Smart Farm Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/aquaponics/raspberry_pi
Environment="PATH=/home/pi/aquaponics-env/bin"
ExecStart=/home/pi/aquaponics-env/bin/python app/main.py --config ../config.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable aquaponics.service
sudo systemctl start aquaponics.service

# Check status
sudo systemctl status aquaponics.service

# View logs
sudo journalctl -u aquaponics.service -f
```

---

## Arduino Setup

### Step 1: Install Arduino IDE

Download from https://www.arduino.cc/en/software

### Step 2: Install Required Libraries

In Arduino IDE:
- Sketch → Include Library → Manage Libraries

Install:
- OneWire (by Jim Studt)
- DallasTemperature (by Miles Burton)
- ArduinoJson (by Benoit Blanchon)
- SD (built-in)

### Step 3: Configure and Upload

1. Open `arduino/main.ino` in Arduino IDE
2. Edit `arduino/config.h` if needed (pin assignments)
3. Select board: Tools → Board → Arduino Mega 2560
4. Select port: Tools → Port → `/dev/ttyUSB0`
5. Click Upload (Ctrl+U)

### Step 4: Verify Operation

- Open Serial Monitor (Ctrl+Shift+M)
- Baud rate: 115200
- Should see sensor readings

---

## Docker Deployment (Optional)

### Create Docker Image

```bash
# Build image
docker build -t aquaponics:latest .

# Run container
docker run -d \
  --name aquaponics \
  -p 5000:5000 \
  -v ~/aquaponics/data:/app/data \
  -v ~/aquaponics/logs:/app/logs \
  --device=/dev/i2c-1:/dev/i2c-1 \
  --device=/dev/ttyUSB0:/dev/ttyUSB0 \
  aquaponics:latest
```

---

## Network Configuration

### Access from Other Devices

```bash
# Find Raspberry Pi IP
hostname -I

# Or find on network
nmap -sn 192.168.1.0/24 | grep -i raspberrypi
```

**Remote Access:**
- Dashboard: `http://<pi-ip>:5000`
- API: `http://<pi-ip>:5000/api`

### Port Forwarding (Optional)

For internet access (requires security hardening):
1. Configure firewall/router port forwarding
2. Enable HTTPS in `config.json`
3. Use reverse proxy (nginx)

---

## Troubleshooting Installation

### Issue: Module Not Found Errors

```bash
# Verify virtual environment is activated
source ~/aquaponics-env/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: Permission Denied for GPIO/I2C

```bash
# Add user to required groups
sudo usermod -a -G gpio pi
sudo usermod -a -G i2c pi

# Reboot for changes to take effect
sudo reboot
```

### Issue: Port Already in Use

```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill process or change port in config.json
```

### Issue: Database Lock

```bash
# Check for running processes
ps aux | grep python

# Remove lock file if necessary
rm data/aquaponics.db-wal
```

---

## Post-Installation

### 1. Initial Calibration

See `CALIBRATION.md` for detailed procedures

### 2. Configure Alert Thresholds

Edit `config.json` to customize alert limits for your system

### 3. Setup Data Backups

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="./data/backups"
mkdir -p $BACKUP_DIR
cp data/aquaponics.db $BACKUP_DIR/aquaponics_$(date +%Y%m%d_%H%M%S).db
echo "Backup created"
EOF

chmod +x backup.sh

# Schedule with cron
crontab -e
# Add: 0 0 * * * /home/pi/aquaponics/backup.sh
```

### 4. Monitor System Performance

```bash
# Check CPU/Memory usage
top

# Check disk space
df -h

# View logs
tail -f logs/aquaponics.log
```

---

## Updating Application

```bash
# Pull latest changes
cd ~/aquaponics
git pull origin main

# Update dependencies
pip install -r raspberry_pi/requirements.txt --upgrade

# Restart service
sudo systemctl restart aquaponics.service
```

---

## Safety Checklist

- [ ] All sensors properly calibrated
- [ ] Power supply adequately rated
- [ ] Network connectivity established
- [ ] Data backups configured
- [ ] Alert thresholds set appropriately
- [ ] Dashboard accessible from web browser
- [ ] Logs being generated properly
- [ ] Auto-start service enabled (if desired)

---

## Getting Help

- Check `TROUBLESHOOTING.md` for common issues
- Review logs: `logs/aquaponics.log`
- Check API health: `http://localhost:5000/health`
- Review sensor readings: `http://localhost:5000/api/current`

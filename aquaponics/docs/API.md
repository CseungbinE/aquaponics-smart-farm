# Aquaponics Smart Farm - API Documentation

## Overview

The Aquaponics Smart Farm system provides a RESTful API for accessing sensor data, managing alerts, calibration, and configuration. The API is built with Flask and returns JSON responses.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Currently, the API has basic authentication through IP-based access control. For production deployment, implement proper authentication (API keys, JWT tokens, etc.).

## Response Format

All API responses follow this structure:

```json
{
  "timestamp": "2025-11-13T12:34:56.789123",
  "status": "success",
  "data": {
    // Response-specific data
  }
}
```

On error:

```json
{
  "error": "Error message description"
}
```

## Endpoints

### Health Check

**GET** `/health`

Check if the system is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-13T12:34:56.789123",
  "version": "1.0.0"
}
```

---

### Get Current Readings

**GET** `/api/current`

Retrieve the latest sensor readings and system status.

**Response:**
```json
{
  "timestamp": "2025-11-13T12:34:56.789123",
  "readings": {
    "pH": 6.8,
    "EC": 1350,
    "temperature": 24.5,
    "DO": 6.2,
    "water_level": 95,
    "turbidity": 50,
    "status": "OK"
  },
  "sensor_health": {
    "pH": {
      "sensor_id": 1,
      "name": "pH",
      "is_healthy": true,
      "last_reading": {
        "value": 6.8,
        "unit": "pH"
      }
    }
    // ... other sensors
  }
}
```

---

### Get Historical Data

**GET** `/api/history`

Retrieve historical sensor data.

**Query Parameters:**
- `days` (optional, default=1): Number of days to retrieve
- `limit` (optional, default=1000): Maximum number of records

**Example:**
```
GET /api/history?days=7&limit=500
```

**Response:**
```json
{
  "timestamp": "2025-11-13T12:34:56.789123",
  "days": 7,
  "count": 342,
  "data": [
    {
      "timestamp": "2025-11-13T12:30:00",
      "pH": 6.8,
      "EC": 1350,
      "temperature": 24.5,
      "DO": 6.2,
      "water_level": 95,
      "turbidity": 50,
      "status": "OK",
      "notes": null
    },
    // ... more readings
  ]
}
```

---

### Get Statistics

**GET** `/api/statistics`

Get statistical analysis of sensor data.

**Query Parameters:**
- `hours` (optional, default=24): Hours to analyze

**Response:**
```json
{
  "timestamp": "2025-11-13T12:34:56.789123",
  "hours": 24,
  "statistics": {
    "pH": {
      "min": 6.5,
      "max": 7.2,
      "avg": 6.85
    },
    "EC": {
      "min": 1300,
      "max": 1400,
      "avg": 1350
    },
    "temperature": {
      "min": 22.0,
      "max": 26.0,
      "avg": 24.5
    },
    "DO": {
      "min": 5.8,
      "max": 6.8,
      "avg": 6.2
    }
  }
}
```

---

### Get Active Alerts

**GET** `/api/alerts/active`

Retrieve all active (unresolved) alerts.

**Response:**
```json
{
  "timestamp": "2025-11-13T12:34:56.789123",
  "count": 2,
  "alerts": [
    {
      "id": 1,
      "timestamp": "2025-11-13T11:30:00",
      "sensor_name": "pH",
      "alert_type": "WARNING",
      "parameter": "pH",
      "value": 5.2,
      "threshold": "5.5-7.5",
      "message": "pH is below optimal",
      "resolved": false,
      "resolved_at": null
    },
    // ... more alerts
  ]
}
```

---

### Get Alerts by Date Range

**GET** `/api/alerts`

Retrieve alerts within a date range.

**Query Parameters:**
- `start_date` (optional): ISO format datetime (default: 7 days ago)
- `end_date` (optional): ISO format datetime (default: now)

**Example:**
```
GET /api/alerts?start_date=2025-11-06T00:00:00&end_date=2025-11-13T23:59:59
```

---

### Create Alert

**POST** `/api/alerts`

Manually trigger an alert.

**Request Body:**
```json
{
  "sensor_name": "pH",
  "alert_type": "WARNING",
  "parameter": "pH",
  "value": 5.2,
  "threshold": "5.5-7.5",
  "message": "pH is below optimal"
}
```

**Response:** (HTTP 201)
```json
{
  "status": "created",
  "alert": {
    "id": 1,
    "timestamp": "2025-11-13T12:34:56.789123",
    "sensor_name": "pH",
    "alert_type": "WARNING",
    // ... alert details
  }
}
```

---

### Resolve Alert

**POST** `/api/alerts/<alert_id>/resolve`

Mark an alert as resolved.

**Response:**
```json
{
  "status": "resolved"
}
```

---

### Calibrate Sensor

**POST** `/api/calibration/<sensor_name>`

Calibrate a specific sensor.

**Sensor Names:** `pH`, `EC`, `temperature`, `DO`, `water_level`, `turbidity`

**Request Body (pH - 3-point):**
```json
{
  "calibration_type": "3-point",
  "points": {
    "low": 200,
    "mid": 512,
    "high": 822
  },
  "notes": "Standard calibration"
}
```

**Request Body (EC - 2-point):**
```json
{
  "calibration_type": "2-point",
  "points": {
    "low": 200,
    "high": 800
  },
  "notes": "EC calibration"
}
```

**Response:**
```json
{
  "status": "calibrated",
  "sensor": "pH",
  "points": {
    "low": 200,
    "mid": 512,
    "high": 822
  }
}
```

---

### Get Calibration Data

**GET** `/api/calibration/<sensor_name>`

Retrieve latest calibration for a sensor.

**Response:** (HTTP 200)
```json
{
  "sensor": "pH",
  "calibration": {
    "timestamp": "2025-11-13T10:00:00",
    "sensor_name": "pH",
    "calibration_type": "3-point",
    "points": "{\"low\": 200, \"mid\": 512, \"high\": 822}",
    "valid": true,
    "notes": "Standard calibration"
  }
}
```

Or (HTTP 404) if no calibration exists.

---

### Get Configuration

**GET** `/api/config`

Retrieve current system configuration.

**Response:**
```json
{
  "config": {
    "hardware": {
      "platform": "raspberry_pi",
      "sensors": {
        // sensor configurations
      }
    },
    "monitoring": {
      "reading_interval_seconds": 300,
      "averaging_window": 10,
      "alert_thresholds": {
        // threshold definitions
      }
    }
  },
  "thresholds": {
    "pH": {
      "min": 5.5,
      "max": 7.5,
      "critical_min": 5.0,
      "critical_max": 8.0
    },
    // ... other thresholds
  }
}
```

---

### Update Configuration

**POST** `/api/config`

Update system configuration.

**Request Body:**
```json
{
  "thresholds": {
    "pH": {
      "min": 6.0,
      "max": 7.5,
      "critical_min": 5.5,
      "critical_max": 8.0
    }
  }
}
```

---

### Export Data

**GET** `/api/export`

Export sensor data in CSV or JSON format.

**Query Parameters:**
- `format` (required): `csv` or `json`
- `hours` (optional, default=24): Hours of data to export

**Examples:**
```
GET /api/export?format=json&hours=24
GET /api/export?format=csv&hours=7*24
```

**JSON Response:**
```json
{
  "timestamp": "2025-11-13T12:34:56.789123",
  "hours": 24,
  "count": 288,
  "data": [
    // sensor readings
  ]
}
```

**CSV Response:**
Returns a file attachment with CSV format:
```
timestamp,pH,EC,temperature,DO,water_level,turbidity,status
2025-11-13T12:30:00,6.8,1350,24.5,6.2,95,50,OK
...
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request parameters"
}
```

### 404 Not Found
```json
{
  "error": "Not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

---

## Rate Limiting

Default rate limits (can be configured):
- 1000 requests per hour per user
- 10000 requests per hour per IP

---

## Example Usage

### Curl Command

Get current readings:
```bash
curl -X GET http://localhost:5000/api/current
```

Get historical data:
```bash
curl -X GET "http://localhost:5000/api/history?days=7&limit=500"
```

Calibrate pH sensor:
```bash
curl -X POST http://localhost:5000/api/calibration/pH \
  -H "Content-Type: application/json" \
  -d '{"calibration_type":"3-point","points":{"low":200,"mid":512,"high":822}}'
```

### Python Example

```python
import requests
import json

BASE_URL = "http://localhost:5000/api"

# Get current readings
response = requests.get(f"{BASE_URL}/current")
data = response.json()
print(f"Current pH: {data['readings']['pH']}")

# Get history
response = requests.get(f"{BASE_URL}/history?days=7")
history = response.json()
print(f"Records: {history['count']}")

# Export data
response = requests.get(f"{BASE_URL}/export?format=json&hours=24")
export_data = response.json()
```

---

## CORS Support

The API supports Cross-Origin Resource Sharing (CORS). Allowed origins are configurable in `config.json`.

---

## Changelog

### Version 1.0.0 (2025-11-13)
- Initial API release
- All core endpoints implemented

# Aquaponics Smart Farm - Calibration Guide

## Introduction

Proper sensor calibration is critical for accurate water quality monitoring. This guide covers calibration procedures for all sensors in the Aquaponics Smart Farm system.

## Calibration Schedule

| Sensor | Frequency | Duration | Stability |
|--------|-----------|----------|-----------|
| pH | Monthly | 5 minutes | ±0.2 pH |
| EC/TDS | Quarterly | 3 minutes | ±10 μS/cm |
| Temperature | Not required | - | Factory calibrated |
| DO | Quarterly | 10 minutes | ±0.5 mg/L |
| Water Level | As needed | 1 minute | Threshold-based |
| Turbidity | Quarterly | 2 minutes | ±5 NTU |

---

## pH Sensor Calibration (3-Point)

### Required Materials

1. **Calibration Solutions:**
   - pH 4.0 buffer solution (acidic)
   - pH 7.0 buffer solution (neutral)
   - pH 10.0 buffer solution (alkaline)

2. **Equipment:**
   - Clean containers (3 small beakers)
   - Distilled water for rinsing
   - Soft cloth or tissue
   - Temperature thermometer

### Step-by-Step Procedure

#### 1. Prepare Calibration Solutions

```
1. Pour each buffer solution into separate beakers
2. Ensure solutions are at room temperature (20-25°C)
3. If solutions are old (>3 months), replace them
```

#### 2. Access Calibration Interface

**Via Web Dashboard:**
```
1. Open dashboard: http://localhost:5000
2. Navigate to Settings → Calibration
3. Select "pH Sensor"
4. Click "Start Calibration"
```

**Via Arduino Serial Monitor:**
```
1. Open Arduino IDE
2. Serial Monitor (Ctrl+Shift+M)
3. Use commands: CALIB_PH:LOW:XXX (replace XXX with raw value)
```

#### 3. Calibration Process

**Point 1: pH 4.0 (Acidic)**

```
1. Place pH sensor probe in pH 4.0 solution
2. Wait 30 seconds for stabilization
3. Record raw analog value displayed
4. In dashboard, click "Calibrate Point 1"
5. Enter value and confirm
```

**Point 2: pH 7.0 (Neutral)**

```
1. Remove sensor from pH 4.0 solution
2. Rinse thoroughly with distilled water
3. Dry with soft cloth
4. Place sensor in pH 7.0 solution
5. Wait 30 seconds
6. Record raw analog value
7. In dashboard, click "Calibrate Point 2"
8. Enter value and confirm
```

**Point 3: pH 10.0 (Alkaline)**

```
1. Remove sensor from pH 7.0 solution
2. Rinse thoroughly with distilled water
3. Dry with soft cloth
4. Place sensor in pH 10.0 solution
5. Wait 30 seconds
6. Record raw analog value
7. In dashboard, click "Calibrate Point 3"
8. Enter value and confirm
```

#### 4. Verify Calibration

```
1. Place sensor in pH 7.0 solution again
2. System should read ~7.0 pH
3. If reading is off by >0.2, repeat calibration
4. Store calibration data (automatically saved)
```

### Troubleshooting pH Calibration

| Issue | Cause | Solution |
|-------|-------|----------|
| Readings drift | Old solutions | Replace with fresh buffers |
| Non-linear response | Contaminated sensor | Clean probe gently |
| Can't stabilize | Temperature mismatch | Wait for temperature to stabilize |

---

## EC/TDS Sensor Calibration (2-Point)

### Required Materials

1. **Calibration Solutions:**
   - 1000 μS/cm reference solution
   - 10000 μS/cm reference solution

2. **Equipment:**
   - Clean containers (2 beakers)
   - Distilled water for rinsing
   - Digital multimeter (optional)

### Procedure

#### 1. Prepare Solutions

```
1. Pour 1000 μS/cm solution into first beaker
2. Pour 10000 μS/cm solution into second beaker
3. Ensure solutions are at room temperature
4. Cover to prevent evaporation/contamination
```

#### 2. Low Point Calibration (1000 μS/cm)

```
1. Place EC sensor in 1000 μS/cm solution
2. Wait 2 minutes for stabilization
3. Record raw analog voltage or value
4. In dashboard: Settings → Calibration → EC
5. Enter low point value
6. Confirm
```

#### 3. High Point Calibration (10000 μS/cm)

```
1. Remove sensor from low solution
2. Rinse with distilled water
3. Pat dry with soft cloth
4. Place sensor in 10000 μS/cm solution
5. Wait 2 minutes for stabilization
6. Record raw analog value
7. In dashboard: Enter high point value
8. Confirm calibration
```

#### 4. Verification

```
1. Place sensor back in 1000 μS/cm solution
2. System should read ~1000 μS/cm
3. If off by >50 μS/cm, repeat calibration
```

### EC Sensor Maintenance

```
After each use:
- Rinse with distilled water
- Pat dry
- Store in dry location

Weekly:
- Check for salt buildup
- If present, soak in distilled water for 30 minutes
- Clean gently with soft brush

Monthly:
- Replace salt solution if cloudy
- Inspect for physical damage
```

---

## DO Sensor Calibration (2-Point)

### Required Materials

1. **Calibration Points:**
   - Zero point: Nitrogen-saturated water or distilled water
   - Span point: Air-saturated water at current temperature

2. **Equipment:**
   - Nitrogen gas (or water boiling setup)
   - Thermometer
   - Clean containers

### Procedure

#### 1. Zero Point Calibration

```
Method A (Nitrogen gas):
1. Bubble nitrogen through water for 5 minutes
2. Place DO sensor in nitrogen-saturated water
3. Wait 60 seconds
4. System should show ~0 mg/L
5. In dashboard: Confirm zero point

Method B (Boiled water):
1. Boil distilled water
2. Cool to room temperature in sealed container
3. Place sensor in cooled water
4. Wait 60 seconds
5. System should show ~0 mg/L
```

#### 2. Span Point Calibration

```
1. Expose water to air in clean container
2. Aerate by stirring or bubbling air for 5 minutes
3. Place DO sensor in air-saturated water
4. Wait 60 seconds
5. Record DO value
6. At sea level, 25°C: should be ~8-8.5 mg/L
7. In dashboard: Confirm span point
```

#### 3. Temperature Compensation

The system automatically compensates for temperature:
```
- Record water temperature during calibration
- System uses temperature-saturation tables
- Recalibrate if operating >5°C from calibration temp
```

### DO Sensor Maintenance

```
Weekly:
- Check membrane for dirt/algae
- Gently wipe with soft cloth if needed

Monthly:
- Replace membrane if damaged
- Check for air bubbles in electrode
- Recalibrate if readings drift >0.5 mg/L

Quarterly:
- Full replacement of sensor if available
- Verify accuracy against lab standards (optional)
```

---

## Water Level Sensor Calibration

Water level sensors are threshold-based (not continuous) and don't require multi-point calibration.

### Adjustment

```
1. Position sensor at desired minimum water level
2. Note GPIO state (HIGH or LOW)
3. In config.json, set water_level_critical_min threshold
4. Test by adding/removing water
5. Verify alert triggers at correct level
```

---

## Turbidity Sensor Calibration

### Required Materials

1. **Calibration Standards:**
   - Clear water (baseline)
   - Optional: NTU standards (50, 100, 500 NTU)

### Procedure

#### 1. Clear Water Baseline

```
1. Use distilled or clear tap water
2. Place turbidity sensor in container
3. Ensure no air bubbles on sensor window
4. Wait 30 seconds for stabilization
5. Record raw analog value as baseline
6. System treats this as 0 NTU
```

#### 2. Verification with Turbid Water

```
1. Add small amount of food coloring or clay
2. Mix thoroughly
3. Place sensor in turbid water
4. System should show higher NTU value
5. If reading seems incorrect, recalibrate
```

---

## Batch Calibration Procedure

To calibrate all sensors at once:

```bash
# Via command line
python app/main.py --calibrate-all

# Or via dashboard:
# Settings → Maintenance → Calibrate All Sensors
```

## Calibration Validation

After calibration, verify with known water samples:

| Scenario | Expected Values |
|----------|-----------------|
| Fresh water | pH: 6.5-7.5, EC: <200 μS/cm, DO: 7-9 mg/L, Turbidity: <5 NTU |
| Aquaponics optimal | pH: 6.8-7.0, EC: 1200-1600 μS/cm, DO: 5-8 mg/L, Turbidity: <100 NTU |
| Salt water | pH: 7.8-8.2, EC: >30000 μS/cm, DO: <6 mg/L (colder) |

---

## Calibration Data Management

### View Calibration History

```bash
# Via API
curl http://localhost:5000/api/calibration/pH

# Via database
sqlite3 data/aquaponics.db "SELECT * FROM calibrations ORDER BY timestamp DESC LIMIT 10;"
```

### Export Calibration Data

```bash
# Export as JSON
curl http://localhost:5000/api/calibration/pH > ph_calib.json

# Archive old calibrations
cp -r data/backups/calibrations data/backups/calibrations_archive_$(date +%Y%m%d)
```

---

## Seasonal Considerations

### Summer
- Higher water temperatures affect calibration
- Recalibrate temperature-dependent sensors (DO, EC)
- More frequent algae growth on sensors

### Winter
- Lower temperatures
- Slower response times
- Ensure antifreeze in outdoor systems

### Spring/Fall
- Temperature fluctuations
- Check calibration more frequently

---

## Advanced Topics

### Multi-Point Calibration (pH)

For high-accuracy applications, use 3-point calibration:
```
- pH 4.0: Acidic benchmark
- pH 7.0: Neutral/midpoint
- pH 10.0: Alkaline benchmark
```

### Temperature Correction

The system provides automatic correction for:
- EC sensors: 2%/°C standard
- DO sensors: Saturation-based correction
- pH sensors: Slope change with temperature

### Verifying Against Lab Standards

For quality assurance:
```
1. Collect water sample
2. Test with system sensors
3. Send to professional lab
4. Compare results
5. Note any significant deviations
6. Recalibrate if error >2%
```

---

## Maintenance Log Template

Keep a calibration record:

```
Date: ___________
Sensor: ___________
Method: ___________
Calibration Points: ___________
Readings After: ___________
Status: ✓ Pass / ✗ Fail
Notes: ___________
Next Calibration: ___________
```

---

## Reference Values

### Optimal Aquaponics Parameters

```
pH: 6.8-7.0 (Nitrobacter optimal)
EC: 1200-1600 μS/cm
Temperature: 20-26°C
DO: 5-8 mg/L
Nitrogen: 150-250 mg/L
Potassium: 200-300 mg/L
Phosphorus: 25-75 mg/L
```

### Sensor Accuracy

| Sensor | Accuracy | Repeatability |
|--------|----------|--------------|
| pH | ±0.1 | ±0.05 |
| EC | ±2% | ±1% |
| Temp | ±0.5°C | ±0.2°C |
| DO | ±0.5 mg/L | ±0.3 mg/L |
| Level | Threshold-based | - |
| Turbidity | ±5 NTU | ±3 NTU |

---

## Support

If calibration issues persist:
1. Check `TROUBLESHOOTING.md`
2. Review sensor data logs
3. Verify solutions are not expired
4. Contact manufacturer for sensor replacement

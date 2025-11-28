/**
 * Aquaponics Smart Farm - Sensor Classes
 * Optimized for DFRobot Gravity Series Sensors
 */

#ifndef SENSORS_H
#define SENSORS_H

#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <EEPROM.h>

// ============================================================
// BASE SENSOR CLASS
// ============================================================

class Sensor {
protected:
  int pin;
  int sensor_id;
  bool enabled;
  uint8_t quality_flags;
  float raw_value;
  float calibration_offset;
  float calibration_scale;

public:
  Sensor(int _pin) : pin(_pin), sensor_id(0), enabled(true), quality_flags(0),
                     raw_value(0.0), calibration_offset(0.0), calibration_scale(1.0) {}

  virtual ~Sensor() {}

  virtual float read() = 0;
  virtual void calibrate() = 0;
  virtual void load_calibration() = 0;
  virtual void save_calibration() = 0;

  uint8_t get_flags() const { return quality_flags; }
  void set_flags(uint8_t flags) { quality_flags = flags; }
  bool is_healthy() const { return quality_flags == SENSOR_OK; }
  float get_raw() const { return raw_value; }
};

// ============================================================
// PH SENSOR CLASS (Target: Gravity SEN0161-V2)
// ============================================================

class PHSensor : public Sensor {
private:
  float calib_low_raw;      // Raw ADC at pH 4.0
  float calib_mid_raw;      // Raw ADC at pH 7.0
  float calib_high_raw;     // Raw ADC at pH 10.0

  float slope_low;          // Slope between pH 4.0 and 7.0
  float slope_high;         // Slope between pH 7.0 and 10.0

public:
  PHSensor(int _pin) : Sensor(_pin),
                       // DFRobot V2 pH 센서는 중성(7.0)에서 약 1.5V 출력 (5V 아두이노 기준 ADC ~307)
                       // 산성(4.0)은 약 2.0V (ADC ~410), 알칼리(10.0)는 약 1.0V (ADC ~205)
                       calib_low_raw(410.0),
                       calib_mid_raw(307.0),
                       calib_high_raw(205.0),
                       slope_low(1.0),
                       slope_high(1.0) {
    sensor_id = 1;
    load_calibration();
  }

  float read() override {
    raw_value = 0.0;
    for (int i = 0; i < 10; i++) { // 평균 샘플링 증가
      raw_value += analogRead(pin);
      delay(5);
    }
    raw_value /= 10.0;

    if (raw_value < 0 || raw_value > 1023) {
      quality_flags |= SENSOR_OUT_OF_RANGE;
      return -1.0;
    }

    float ph_value = 7.0;

    // 3-Point Calibration Logic (Piecewise Linear)
    if (raw_value > calib_mid_raw) { 
      // V2 센서는 pH가 낮을수록 전압이 높습니다 (산성 영역)
      if (calib_low_raw != calib_mid_raw) {
         slope_low = (7.0 - 4.0) / (calib_low_raw - calib_mid_raw); // 기울기 계산
         ph_value = 7.0 - slope_low * (raw_value - calib_mid_raw);
      }
    } else {
      // 알칼리 영역
      if (calib_mid_raw != calib_high_raw) {
         slope_high = (10.0 - 7.0) / (calib_mid_raw - calib_high_raw);
         ph_value = 7.0 + slope_high * (calib_mid_raw - raw_value);
      }
    }

    quality_flags = SENSOR_OK;
    return constrain(ph_value, 0.0, 14.0);
  }

  void calibrate() override {} // Main sketch handles serial commands

  void load_calibration() override {
    EEPROM.get(EEPROM_PH_CALIB_LOW_ADDR, calib_low_raw);
    EEPROM.get(EEPROM_PH_CALIB_MID_ADDR, calib_mid_raw);
    EEPROM.get(EEPROM_PH_CALIB_HIGH_ADDR, calib_high_raw);
  }

  void save_calibration() override {
    EEPROM.put(EEPROM_PH_CALIB_LOW_ADDR, calib_low_raw);
    EEPROM.put(EEPROM_PH_CALIB_MID_ADDR, calib_mid_raw);
    EEPROM.put(EEPROM_PH_CALIB_HIGH_ADDR, calib_high_raw);
  }

  void set_calib_low(float raw) { calib_low_raw = raw; }
  void set_calib_mid(float raw) { calib_mid_raw = raw; }
  void set_calib_high(float raw) { calib_high_raw = raw; }
};

// ============================================================
// EC SENSOR CLASS (Target: Gravity SEN0244 TDS Sensor)
// Note: This sensor measures TDS (ppm). We convert to EC (uS/cm).
// ============================================================

class ECSensor : public Sensor {
private:
  float calib_low_raw;      // Raw ADC at Low Standard
  float calib_high_raw;     // Raw ADC at High Standard
  float last_temperature;   

public:
  ECSensor(int _pin) : Sensor(_pin),
                       // SEN0244 출력 범위: 0 ~ 2.3V
                       // 5V Arduino ADC 기준: 0 ~ 471
                       calib_low_raw(50.0),    // 대략적인 Low Point
                       calib_high_raw(400.0),  // 대략적인 High Point (2.3V 근처)
                       last_temperature(25.0) {
    sensor_id = 2;
    load_calibration();
  }

  float read() override {
    raw_value = 0.0;
    for (int i = 0; i < 10; i++) {
      raw_value += analogRead(pin);
      delay(5);
    }
    raw_value /= 10.0;

    // SEN0244는 전압이 2.3V를 넘지 않음
    if (raw_value < 0 || raw_value > 1023) {
      quality_flags |= SENSOR_OUT_OF_RANGE;
      return -1.0;
    }

    // 1. Calculate TDS (ppm) using 2-Point Calibration
    // config.h의 EC_CALIB 값들은 uS/cm 단위이므로, 
    // 여기서 ppm으로 매핑하기 위해 0.5를 곱해 TDS 기준으로 기울기를 구합니다.
    // (일반적인 변환: 1 EC (uS/cm) = 0.5 TDS (ppm))
    
    float tds_low = EC_CALIB_LOW * 0.5;
    float tds_high = EC_CALIB_HIGH * 0.5;
    
    float slope = (tds_high - tds_low) / (calib_high_raw - calib_low_raw);
    float tds_value = tds_low + slope * (raw_value - calib_low_raw);

    // 2. Temperature Compensation for TDS
    float temp_factor = 1.0 + 0.02 * (last_temperature - 25.0); // 2% per degC
    if (temp_factor > 0) {
        tds_value /= temp_factor;
    }

    // 3. Convert TDS (ppm) back to EC (uS/cm) for system consistency
    float ec_value = tds_value * 2.0; 

    quality_flags = SENSOR_OK;
    return constrain(ec_value, 0.0, 20000.0);
  }

  void calibrate() override {}

  void load_calibration() override {
    EEPROM.get(EEPROM_EC_CALIB_LOW_ADDR, calib_low_raw);
    EEPROM.get(EEPROM_EC_CALIB_HIGH_ADDR, calib_high_raw);
  }

  void save_calibration() override {
    EEPROM.put(EEPROM_EC_CALIB_LOW_ADDR, calib_low_raw);
    EEPROM.put(EEPROM_EC_CALIB_HIGH_ADDR, calib_high_raw);
  }

  void set_temperature(float temp) { last_temperature = temp; }
  void set_calib_low(float raw) { calib_low_raw = raw; }
  void set_calib_high(float raw) { calib_high_raw = raw; }
};

// ============================================================
// TEMPERATURE SENSOR CLASS (Target: DFR0194 / DS18B20)
// ============================================================

class TemperatureSensor : public Sensor {
private:
  OneWire* one_wire;
  DallasTemperature* sensors;

public:
  TemperatureSensor(int _pin) : Sensor(_pin) {
    sensor_id = 3;
    one_wire = new OneWire(_pin);
    sensors = new DallasTemperature(one_wire);
    sensors->begin();
  }

  ~TemperatureSensor() {
    delete sensors;
    delete one_wire;
  }

  float read() override {
    sensors->requestTemperatures();
    // DS18B20 변환 대기 시간은 해상도에 따라 다르지만 800ms면 충분함
    
    raw_value = sensors->getTempCByIndex(0);

    if (raw_value == DEVICE_DISCONNECTED_C || raw_value < -50.0) {
      quality_flags |= SENSOR_ERROR;
      return -999.0;
    }

    quality_flags = SENSOR_OK;
    return raw_value;
  }

  void calibrate() override {}
  void load_calibration() override {}
  void save_calibration() override {}
};

// ============================================================
// DO SENSOR CLASS (Target: Gravity SEN0237)
// ============================================================

class DOSensor : public Sensor {
private:
  float calib_do_raw;       // ADC at 100% saturation
  float last_temperature;

public:
  DOSensor(int _pin) : Sensor(_pin),
                       calib_do_raw(327.0), // SEN0237 Saturation Voltage ~1.6V (ADC ~327 @ 5V)
                       last_temperature(25.0) {
    sensor_id = 4;
    load_calibration();
  }

  float read() override {
    raw_value = 0.0;
    for (int i = 0; i < 10; i++) {
      raw_value += analogRead(pin);
      delay(5);
    }
    raw_value /= 10.0;

    // Calculate Saturation Concentration (mg/L) based on temp
    float saturation_mg_L = 14.652 - 0.41022 * last_temperature + 0.007991 * last_temperature * last_temperature - 0.000077774 * last_temperature * last_temperature * last_temperature;
    
    // Ratio calculation
    float ratio = raw_value / calib_do_raw;
    float do_value = ratio * saturation_mg_L;

    quality_flags = SENSOR_OK;
    return constrain(do_value, 0.0, 20.0);
  }

  void calibrate() override {
    float current_raw = 0.0;
    for(int i=0; i<10; i++) {
        current_raw += analogRead(pin);
        delay(10);
    }
    calib_do_raw = current_raw / 10.0;
    save_calibration();
  }

  void set_calib_span(float raw) { calib_do_raw = raw; }
  void set_calib_zero(float raw) {} 

  void load_calibration() override {
    EEPROM.get(EEPROM_DO_CALIB_SPAN_ADDR, calib_do_raw);
    if(calib_do_raw < 10 || calib_do_raw > 1000) calib_do_raw = 327.0;
  }

  void save_calibration() override {
    EEPROM.put(EEPROM_DO_CALIB_SPAN_ADDR, calib_do_raw);
  }

  void set_temperature(float temp) { last_temperature = temp; }
};

// ============================================================
// WATER LEVEL SENSOR CLASS (Generic Analog)
// ============================================================

class WaterLevelSensor : public Sensor {
private:
  float tank_height_mm;    
  float sensor_max_mm;     
  float voltage_full;      

public:
  WaterLevelSensor(int _pin) : Sensor(_pin), 
                               tank_height_mm(1000.0), // ★ 실제 물탱크 높이(mm)로 수정하세요!
                               sensor_max_mm(5000.0),  // 센서 스펙상 최대 깊이
                               voltage_full(2.3)       // 예상 최대 전압 (센서에 따라 조정)
  {
    sensor_id = 5;
  }

  float read() override {
    float total_raw = 0.0;
    for (int i = 0; i < 10; i++) {
      total_raw += analogRead(pin);
      delay(5);
    }
    float avg_raw = total_raw / 10.0;
    
    // Convert to Voltage (5V Ref)
    float voltage = avg_raw * (5.0 / 1023.0);
    
    // Calculate Depth & Percentage
    float depth_mm = 0.0;
    if (voltage > 0.05) { // Noise filter
        depth_mm = (voltage / voltage_full) * sensor_max_mm;
    }
    
    float percentage = (depth_mm / tank_height_mm) * 100.0;

    quality_flags = SENSOR_OK;
    return constrain(percentage, 0.0, 100.0);
  }

  void calibrate() override {}
  void load_calibration() override {}
  void save_calibration() override {}
};

// ============================================================
// TURBIDITY SENSOR CLASS (Target: Gravity SEN0189)
// ============================================================

class TurbiditySensor : public Sensor {
private:
  float calib_clear_raw;  // Baseline voltage for clear water

public:
  TurbiditySensor(int _pin) : Sensor(_pin), calib_clear_raw(800.0) { // SEN0189 Clear water is usually ~4V (ADC ~818)
    sensor_id = 6;
    load_calibration();
  }

  float read() override {
    raw_value = 0.0;
    for (int i = 0; i < 5; i++) {
      raw_value += analogRead(pin);
      delay(5);
    }
    raw_value /= 5.0;

    if (raw_value < 0 || raw_value > 1023) {
      quality_flags |= SENSOR_OUT_OF_RANGE;
      return -1.0;
    }

    // Simple inverted percentage for turbidity
    // SEN0189: High Voltage = Clear, Low Voltage = Turbid
    float turbidity = 0.0;
    if (raw_value < calib_clear_raw) {
        turbidity = ((calib_clear_raw - raw_value) / calib_clear_raw) * 1000.0;
    }

    quality_flags = SENSOR_OK;
    return constrain(turbidity, 0.0, 1000.0);
  }

  void calibrate() override {
      // Set current reading as "Clear Water" baseline
      float total = 0;
      for(int i=0; i<10; i++) { total += analogRead(pin); delay(5); }
      calib_clear_raw = total / 10.0;
      save_calibration();
  }

  void load_calibration() override {
     // For simplicity, using default or implemented EEPROM logic if needed
     // Here using constructor default
  }

  void save_calibration() override {}
  void set_calib_clear(float raw) { calib_clear_raw = raw; }
};

#endif // SENSORS_H
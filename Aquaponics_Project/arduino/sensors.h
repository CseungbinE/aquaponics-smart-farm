/**
 * Aquaponics Smart Farm - Sensor Classes
 * Implements interfaces for pH, EC, Temperature, DO, Water Level, and Turbidity sensors
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
// PH SENSOR CLASS
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
                       calib_low_raw(450.0),  // pH 4.0 (산성) 예상 ADC 값 (약 2.2V)
                       calib_mid_raw(307.0),  // pH 7.0 (중성) ADC 값 (1.5V = 약 307)
                       calib_high_raw(160.0), // pH 10.0 (알칼리) 예상 ADC 값 (약 0.8V)
                       slope_low(1.0),
                       slope_high(1.0) {
    sensor_id = 1;
    load_calibration();
  }

  float read() override {
    raw_value = 0.0;

    // Read analog value multiple times and average
    for (int i = 0; i < 5; i++) {
      raw_value += analogRead(pin);
      delay(10);
    }
    raw_value /= 5.0;

    // Validate range
    if (raw_value < 0 || raw_value > 1023) {
      quality_flags |= SENSOR_OUT_OF_RANGE;
      return -1.0;
    }

    // Convert to pH using 3-point calibration
    float ph_value = 0.0;

    if (raw_value < calib_mid_raw) {
      // Between pH 4.0 and 7.0
      // V2 센서는 산성일수록 전압이 높으므로(450 > 307), raw_value가 mid보다 크면 산성 영역입니다.
      // 하지만 코드는 범용성을 위해 로직을 그대로 둡니다. (slope 계산이 자동 보정함)
      if (calib_low_raw != calib_mid_raw) {
         slope_low = (7.0 - 4.0) / (calib_mid_raw - calib_low_raw);
         ph_value = 4.0 + slope_low * (raw_value - calib_low_raw);
      }
    } else {
      // Between pH 7.0 and 10.0
      if (calib_high_raw != calib_mid_raw) {
         slope_high = (10.0 - 7.0) / (calib_high_raw - calib_mid_raw);
         ph_value = 7.0 + slope_high * (raw_value - calib_mid_raw);
      }
    }

    quality_flags = SENSOR_OK;
    return constrain(ph_value, 0.0, 14.0);
  }

  void calibrate() override {
    // Implementation done in main sketch
  }

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
// EC/TDS SENSOR CLASS (SEN0451 PRO Optimized)
// ============================================================

class ECSensor : public Sensor {
private:
  float calib_low_raw;      // Raw ADC at EC 1413 uS/cm
  float calib_high_raw;     // Raw ADC at EC 12880 uS/cm
  float last_temperature;   // For temperature compensation

public:
  ECSensor(int _pin) : Sensor(_pin),
                       // [수정됨] SEN0451 (0~3.0V 출력) 기준 초기값 설정
                       // Arduino 5V 기준: 3.0V는 약 614입니다.
                       // 대략 1413us(Low)는 0.2~0.3V 근처, 12880us(High)는 2.0~2.2V 근처로 예상
                       calib_low_raw(45.0),    // 초기 추정값 (Low Point)
                       calib_high_raw(450.0),  // 초기 추정값 (High Point)
                       last_temperature(25.0) {
    sensor_id = 2;
    load_calibration();
  }

  float read() override {
    raw_value = 0.0;

    // 1. 읽기 및 평균 (노이즈 필터링)
    for (int i = 0; i < 5; i++) {
      raw_value += analogRead(pin);
      delay(10);
    }
    raw_value /= 5.0;

    // 2. 범위 체크
    if (raw_value < 0 || raw_value > 1023) {
      quality_flags |= SENSOR_OUT_OF_RANGE;
      return -1.0;
    }

    // 3. EC 변환 로직 (2-Point Linear Interpolation)
    // 캘리브레이션 용액 기준: Low(1413), High(12880)을 많이 사용함
    // config.h의 EC_CALIB_LOW / HIGH 값과 매핑됨
    
    // 기울기 계산
    float slope = (12880.0 - 1413.0) / (calib_high_raw - calib_low_raw);
    
    // 현재 값 계산
    float ec_value = 1413.0 + slope * (raw_value - calib_low_raw);

    // 4. 온도 보정 (2.0% per °C)
    // 온도가 높으면 전기가 더 잘 통하므로, 25도 기준으로 낮춰서 계산
    float temp_factor = 1.0 + EC_TEMP_COEFF * (last_temperature - 25.0) / 100.0;
    if (temp_factor > 0) {
      ec_value /= temp_factor;
    }

    quality_flags = SENSOR_OK;
    return constrain(ec_value, 0.0, 20000.0); // SEN0451 Max 20ms/cm
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
// TEMPERATURE SENSOR CLASS (DS18B20)
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
    delay(800);  // Wait for conversion

    raw_value = sensors->getTempCByIndex(0);

    // Check for error
    if (raw_value == DEVICE_DISCONNECTED_C) {
      quality_flags |= SENSOR_ERROR;
      return -999.0;
    }

    if (raw_value < -10.0 || raw_value > 85.0) {
      quality_flags |= SENSOR_OUT_OF_RANGE;
      return -999.0;
    }

    quality_flags = SENSOR_OK;
    return raw_value;
  }

  void calibrate() override {}

  void load_calibration() override {
    // DS18B20 is factory calibrated
  }

  void save_calibration() override {
    // DS18B20 is factory calibrated
  }
};

// ============================================================
// DISSOLVED OXYGEN SENSOR CLASS
// ============================================================

class DOSensor : public Sensor {
private:
  float calib_zero_raw;
  float calib_span_raw;
  float last_temperature;

public:
  DOSensor(int _pin) : Sensor(_pin),
                       calib_zero_raw(0.0),
                       calib_span_raw(1023.0),
                       last_temperature(25.0) {
    sensor_id = 4;
    load_calibration();
  }

  float read() override {
    raw_value = 0.0;

    for (int i = 0; i < 5; i++) {
      raw_value += analogRead(pin);
      delay(10);
    }
    raw_value /= 5.0;

    if (raw_value < 0 || raw_value > 1023) {
      quality_flags |= SENSOR_OUT_OF_RANGE;
      return -1.0;
    }

    // Linear conversion: zero to span
    float percentage = ((raw_value - calib_zero_raw) / (calib_span_raw - calib_zero_raw)) * 100.0;

    // Convert percentage to mg/L (assuming 100% = 10 mg/L at sea level, 25°C)
    // Temperature compensation: higher temp = lower saturation
    float do_saturation = 10.0;
    float temp_correction = 1.0 - (last_temperature - 25.0) * 0.03;
    float do_value = (percentage / 100.0) * do_saturation * temp_correction;

    quality_flags = SENSOR_OK;
    return constrain(do_value, 0.0, 20.0);
  }

  void calibrate() override {}

  void load_calibration() override {
    EEPROM.get(EEPROM_DO_CALIB_ZERO_ADDR, calib_zero_raw);
    EEPROM.get(EEPROM_DO_CALIB_SPAN_ADDR, calib_span_raw);
  }

  void save_calibration() override {
    EEPROM.put(EEPROM_DO_CALIB_ZERO_ADDR, calib_zero_raw);
    EEPROM.put(EEPROM_DO_CALIB_SPAN_ADDR, calib_span_raw);
  }

  void set_temperature(float temp) { last_temperature = temp; }
  void set_calib_zero(float raw) { calib_zero_raw = raw; }
  void set_calib_span(float raw) { calib_span_raw = raw; }
};

// ============================================================
// WATER LEVEL SENSOR CLASS (For KIT0139 / Analog)
// ============================================================

class WaterLevelSensor : public Sensor {
private:
  float tank_height_mm;    // 내 물탱크의 전체 높이 (mm)
  float sensor_max_mm;     // 센서가 측정 가능한 최대 깊이 (KIT0139는 보통 5000mm)
  
  // 캘리브레이션용 상수 (4-20mA를 0-5V로 변환 시)
  // 보통 120옴 저항 사용 시: 4mA = 0.48V, 20mA = 2.4V 정도 나옴
  // 정확한 값은 설치 후 시리얼 모니터 보며 조정 필요
  float voltage_empty;     // 물이 없을 때 센서 전압 (V)
  float voltage_full;      // 센서 최대치일 때 전압 (V)

public:
  // 생성자: 핀 번호
  WaterLevelSensor(int _pin) : Sensor(_pin), 
                               tank_height_mm(1000.0), // ★내 물탱크 높이(mm)로 수정하세요! (예: 1m = 1000.0)
                               sensor_max_mm(5000.0),  // 센서 스펙: 5m
                               voltage_empty(0.48),    // 4mA 일 때 예상 전압 (설치 후 보정 필요)
                               voltage_full(2.4)       // 20mA 일 때 예상 전압
  {
    sensor_id = 5;
    // 아날로그 핀은 pinMode 설정 불필요
  }

  float read() override {
    float total_raw = 0.0;
    
    // 1. 아날로그 값 읽기 (평균내기)
    for (int i = 0; i < 10; i++) {
      total_raw += analogRead(pin);
      delay(10);
    }
    float avg_raw = total_raw / 10.0;
    
    // 2. 전압으로 변환 (Arduino Mega: 5.0V 기준)
    float voltage = avg_raw * (5.0 / 1023.0);
    
    // 3. 전압을 수심(mm)으로 변환 (선형 보간)
    // 수심 = (현재전압 - 0수심전압) * (최대수심 / (최대전압 - 0수심전압))
    float depth_mm = (voltage - voltage_empty) * (sensor_max_mm / (voltage_full - voltage_empty));
    
    // 4. 음수 값 보정 (노이즈)
    if (depth_mm < 0) depth_mm = 0;

    // 5. 탱크 높이 대비 퍼센트(%) 계산
    float percentage = (depth_mm / tank_height_mm) * 100.0;

    quality_flags = SENSOR_OK;
    return constrain(percentage, 0.0, 100.0); // 0~100% 사이로 자름
  }

  void calibrate() override {
    // 필요 시 현재 수위를 0% 또는 100%로 설정하는 기능 구현 가능
  }
  
  void load_calibration() override {}
  void save_calibration() override {}
};

// ============================================================
// TURBIDITY SENSOR CLASS
// ============================================================

class TurbiditySensor : public Sensor {
private:
  float calib_clear_raw;  // Raw value for clear water (baseline)

public:
  TurbiditySensor(int _pin) : Sensor(_pin), calib_clear_raw(1023.0) {
    sensor_id = 6;
    load_calibration();
  }

  float read() override {
    raw_value = 0.0;

    for (int i = 0; i < 5; i++) {
      raw_value += analogRead(pin);
      delay(10);
    }
    raw_value /= 5.0;

    if (raw_value < 0 || raw_value > 1023) {
      quality_flags |= SENSOR_OUT_OF_RANGE;
      return -1.0;
    }

    // Conversion formula: NTU = (raw_value / calib_clear_raw) * max_turbidity
    // Assuming sensor range 0-1000 NTU
    float turbidity = ((calib_clear_raw - raw_value) / calib_clear_raw) * 1000.0;

    quality_flags = SENSOR_OK;
    return constrain(turbidity, 0.0, 1000.0);
  }

  void calibrate() override {}

  void load_calibration() override {
    // Load clear water baseline - should be done during setup
    // For now, use default (clear water = max voltage)
  }

  void save_calibration() override {
    // Save clear water baselineE
   }

  void set_calib_clear(float raw) { calib_clear_raw = raw; }
};

#endif // SENSORS_H

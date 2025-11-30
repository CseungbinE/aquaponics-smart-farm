/**
 * Aquaponics Smart Farm - Arduino Main Sketch
 * Real-time water quality monitoring system
 *
 * Board: Arduino Mega 2560
 * Sensors: pH, EC, Temperature, DO, Water Level, Turbidity
 */

#include "config.h"
#include "sensors.h"

#include <Wire.h>
#include <SD.h>
#include <time.h>
#include <avr/wdt.h>  // [수정] Watchdog Timer 라이브러리 추가

// ============================================================
// GLOBAL OBJECTS
// ============================================================

PHSensor        ph_sensor(PH_SENSOR_PIN);
ECSensor        ec_sensor(EC_SENSOR_PIN);
TemperatureSensor temp_sensor(TEMPERATURE_PIN);
DOSensor        do_sensor(DO_SENSOR_PIN);
WaterLevelSensor water_level_sensor(WATER_LEVEL_PIN);
TurbiditySensor turbidity_sensor(TURBIDITY_SENSOR_PIN);

AlertThresholds thresholds;

// Sensor data buffers (for averaging)
float ph_buffer[AVERAGING_WINDOW];
float ec_buffer[AVERAGING_WINDOW];
float temp_buffer[AVERAGING_WINDOW];
float do_buffer[AVERAGING_WINDOW];
float level_buffer[AVERAGING_WINDOW];
float turbidity_buffer[AVERAGING_WINDOW];

int buffer_index = 0;
unsigned long last_reading_time = 0;
unsigned long last_sd_write_time = 0;

File data_file;

// ============================================================
// SETUP
// ============================================================

void setup() {
  // [수정] 안전장치: 부팅 직후 혹시 켜져 있을지 모를 워치독 비활성화
  // (일부 부트로더에서 무한 리셋 루프 방지)
  wdt_disable();

  // Serial communication
  Serial.begin(BAUD_RATE);
  delay(2000);  // Wait for serial to stabilize

  if (DEBUG_SERIAL) {
    Serial.println(F("\n=== Aquaponics Smart Farm - Arduino ==="));
    Serial.println(F("Initializing sensors..."));
  }

  // Initialize I2C for RTC
  Wire.begin();

  // Initialize SD card
  if (ENABLE_SD_LOGGING) {
    if (!SD.begin(SD_CHIP_SELECT_PIN)) {
      if (DEBUG_SERIAL) Serial.println(F("ERROR: SD card initialization failed!"));
    } else {
      if (DEBUG_SERIAL) Serial.println(F("SD card initialized successfully"));
    }
  }

  // Load calibration data from EEPROM
  if (DEBUG_SERIAL) Serial.println(F("Loading calibration data..."));
  ph_sensor.load_calibration();
  ec_sensor.load_calibration();
  do_sensor.load_calibration();
  turbidity_sensor.load_calibration();

  // Load thresholds from EEPROM (or use defaults)
  load_thresholds();

  // Initialize buffers
  init_buffers();

  if (DEBUG_SERIAL) {
    Serial.println(F("Setup complete!"));
    Serial.println(F("Starting sensor readings...\n"));
    print_header();
  }
}

// ============================================================
// MAIN LOOP
// ============================================================

void loop() {
  unsigned long current_time = millis();

  // [중요] 비동기 센서 업데이트 (Non-blocking)
  // 매 루프마다 호출하여 백그라운드에서 데이터를 수집하게 합니다.
  ph_sensor.update();
  ec_sensor.update();
  temp_sensor.update();
  do_sensor.update();
  water_level_sensor.update();
  turbidity_sensor.update();

  // Read sensors at configured interval (데이터 전송 주기)
  if (current_time - last_reading_time >= SENSOR_READ_INTERVAL) {
    read_all_sensors(); // 이제 이 함수는 0ms만에 실행됩니다.
    last_reading_time = current_time;
    buffer_index = (buffer_index + 1) % AVERAGING_WINDOW;

    // Log to SD card
    if (ENABLE_SD_LOGGING && (current_time - last_sd_write_time >= (SD_LOG_INTERVAL * 1000))) {
      log_to_sd();
      last_sd_write_time = current_time;
    }

    // Send to Raspberry Pi via serial
    send_serial_data();

    // Print to Serial Monitor
    if (DEBUG_SERIAL) {
      print_readings();
    }
  }

  // Check for serial commands (for calibration, etc.)
  if (Serial.available()) {
    handle_serial_command();
  }

  delay(100);  // Small delay to prevent overwhelming the loop
}

// ============================================================
// SENSOR READING FUNCTIONS
// ============================================================

void read_all_sensors() {
  // Read each sensor and store in buffer
  float temp = temp_sensor.read();
  if (temp_sensor.is_healthy()) {
    temp_buffer[buffer_index] = temp;
  }

  // Temperature is needed for EC and DO compensation
  ec_sensor.set_temperature(temp);
  do_sensor.set_temperature(temp);

  // Read other sensors
  float ph = ph_sensor.read();
  if (ph_sensor.is_healthy()) {
    ph_buffer[buffer_index] = ph;
  }

  float ec = ec_sensor.read();
  if (ec_sensor.is_healthy()) {
    ec_buffer[buffer_index] = ec;
  }

  float dissolved_oxygen = do_sensor.read();
  if (do_sensor.is_healthy()) {
    do_buffer[buffer_index] = dissolved_oxygen;
  }

  float level = water_level_sensor.read();
  if (water_level_sensor.is_healthy()) {
    level_buffer[buffer_index] = level;
  }

  float turbidity = turbidity_sensor.read();
  if (turbidity_sensor.is_healthy()) {
    turbidity_buffer[buffer_index] = turbidity;
  }
}

float get_average(float* buffer) {
  float sum = 0.0;
  for (int i = 0; i < AVERAGING_WINDOW; i++) {
    sum += buffer[i];
  }
  return sum / AVERAGING_WINDOW;
}

// ============================================================
// SD CARD LOGGING
// ============================================================

void log_to_sd() {
  if (!ENABLE_SD_LOGGING) return;

  // Open file for writing (append mode)
  data_file = SD.open(SD_DATA_FILENAME, FILE_WRITE);

  if (!data_file) {
    if (DEBUG_SERIAL) Serial.println(F("ERROR: Could not open SD file"));
    return;
  }

  // Write header if file is new
  if (data_file.size() == 0) {
    data_file.print(CSV_HEADER);
  }

  // Get current timestamp
  unsigned long timestamp = millis() / 1000; // Seconds since start

  // Format and write CSV line
  char line[128];
  // %5.1f : 수위를 소수점 1자리까지 저장 (예: 95.5)
  snprintf(line, sizeof(line), "%lu,%5.2f,%6.1f,%5.2f,%4.2f,%5.1f,%5.1f,OK\n",
           timestamp,
           get_average(ph_buffer),
           get_average(ec_buffer),
           get_average(temp_buffer),
           get_average(do_buffer),
           get_average(level_buffer),
           get_average(turbidity_buffer));
  
  data_file.print(line);
  data_file.close();

  if (DEBUG_SERIAL) Serial.println(F("Data logged to SD"));
}

// ============================================================
// SERIAL COMMUNICATION
// ============================================================

void send_serial_data() {
  // Send data to Raspberry Pi in JSON format
  // Format: {"pH": 6.8, "EC": 1350, "Temp": 24.5, "DO": 6.2, "Level": 95, "Turbidity": 50}

  Serial.print(F("{\"timestamp\":"));
  Serial.print(millis() / 1000);
  Serial.print(F(",\"pH\":"));
  Serial.print(get_average(ph_buffer), 2);
  Serial.print(F(",\"EC\":"));
  Serial.print(get_average(ec_buffer), 1);
  Serial.print(F(",\"Temp\":"));
  Serial.print(get_average(temp_buffer), 2);
  Serial.print(F(",\"DO\":"));
  Serial.print(get_average(do_buffer), 2);
  Serial.print(F(",\"Level\":"));
  Serial.print(get_average(level_buffer), 1); // 1: 소수점 1자리 출력
  Serial.print(F(",\"Turbidity\":"));
  Serial.print(get_average(turbidity_buffer), 1);
  Serial.println(F("}"));
}

void handle_serial_command() {
  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command.startsWith("CALIB_PH")) {
    handle_ph_calibration(command);
  } else if (command.startsWith("CALIB_EC")) {
    handle_ec_calibration(command);
  } else if (command.startsWith("CALIB_DO")) {
    handle_do_calibration(command);
  } else if (command.startsWith("CALIB_TURB")) {
    handle_turbidity_calibration(command);
  } else if (command == "STATUS") {
    print_status();
  } else if (command == "RESET") {
    software_reset();
  }
}

// ============================================================
// CALIBRATION FUNCTIONS
// ============================================================

void handle_ph_calibration(String cmd) {
  // Command format: CALIB_PH:LOW:512 or CALIB_PH:MID:512 or CALIB_PH:HIGH:512
  int idx1 = cmd.indexOf(':');
  int idx2 = cmd.indexOf(':', idx1 + 1);

  if (idx1 == -1 || idx2 == -1) {
    Serial.println(F("ERROR: Invalid calibration format"));
    return;
  }

  String point = cmd.substring(idx1 + 1, idx2);
  float raw_value = cmd.substring(idx2 + 1).toFloat();

  if (point == "LOW") {
    ph_sensor.set_calib_low(raw_value);
    Serial.println(F("pH calibration LOW stored"));
  } else if (point == "MID") {
    ph_sensor.set_calib_mid(raw_value);
    Serial.println(F("pH calibration MID stored"));
  } else if (point == "HIGH") {
    ph_sensor.set_calib_high(raw_value);
    Serial.println(F("pH calibration HIGH stored"));
  }

  ph_sensor.save_calibration();
  Serial.println(F("pH calibration saved to EEPROM"));
}

void handle_ec_calibration(String cmd) {
  int idx1 = cmd.indexOf(':');
  int idx2 = cmd.indexOf(':', idx1 + 1);

  if (idx1 == -1 || idx2 == -1) {
    Serial.println(F("ERROR: Invalid calibration format"));
    return;
  }

  String point = cmd.substring(idx1 + 1, idx2);
  float raw_value = cmd.substring(idx2 + 1).toFloat();

  if (point == "LOW") {
    ec_sensor.set_calib_low(raw_value);
    Serial.println(F("EC calibration LOW stored"));
  } else if (point == "HIGH") {
    ec_sensor.set_calib_high(raw_value);
    Serial.println(F("EC calibration HIGH stored"));
  }

  ec_sensor.save_calibration();
  Serial.println(F("EC calibration saved to EEPROM"));
}

void handle_do_calibration(String cmd) {
  int idx1 = cmd.indexOf(':');
  int idx2 = cmd.indexOf(':', idx1 + 1);

  if (idx1 == -1 || idx2 == -1) {
    Serial.println(F("ERROR: Invalid calibration format"));
    return;
  }

  String point = cmd.substring(idx1 + 1, idx2);
  float raw_value = cmd.substring(idx2 + 1).toFloat();

  if (point == "ZERO") {
    do_sensor.set_calib_zero(raw_value);
    Serial.println(F("DO calibration ZERO stored"));
  } else if (point == "SPAN") {
    do_sensor.set_calib_span(raw_value);
    Serial.println(F("DO calibration SPAN stored"));
  }

  do_sensor.save_calibration();
  Serial.println(F("DO calibration saved to EEPROM"));
}

void handle_turbidity_calibration(String cmd) {
  int idx = cmd.indexOf(':');
  if (idx == -1) {
    Serial.println(F("ERROR: Invalid calibration format"));
    return;
  }

  float raw_value = cmd.substring(idx + 1).toFloat();
  turbidity_sensor.set_calib_clear(raw_value);
  turbidity_sensor.save_calibration();
  Serial.println(F("Turbidity calibration saved to EEPROM"));
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

void init_buffers() {
  for (int i = 0; i < AVERAGING_WINDOW; i++) {
    ph_buffer[i] = 0.0;
    ec_buffer[i] = 0.0;
    temp_buffer[i] = 0.0;
    do_buffer[i] = 0.0;
    level_buffer[i] = 0.0;
    turbidity_buffer[i] = 0.0;
  }
}

void load_thresholds() {
  // Load from EEPROM or use defaults
}

void print_header() {
  Serial.println(F("Time(s),  pH, EC(μS), Temp(C), DO(mg/L), Level(%), Turbidity(NTU)"));
  Serial.println(F("================================================================="));
}

void print_readings() {
  Serial.print(millis() / 1000);
  Serial.print(F(","));
  Serial.print(get_average(ph_buffer), 2);
  Serial.print(F(","));
  Serial.print(get_average(ec_buffer), 0);
  Serial.print(F(","));
  Serial.print(get_average(temp_buffer), 2);
  Serial.print(F(","));
  Serial.print(get_average(do_buffer), 2);
  Serial.print(F(","));
  Serial.print(get_average(level_buffer), 0);
  Serial.print(F(","));
  Serial.println(get_average(turbidity_buffer), 1);
}

void print_status() {
  Serial.println(F("\n=== System Status ==="));
  Serial.print(F("pH Sensor: "));
  Serial.println(ph_sensor.is_healthy() ? "OK" : "ERROR");
  Serial.print(F("EC Sensor: "));
  Serial.println(ec_sensor.is_healthy() ? "OK" : "ERROR");
  Serial.print(F("Temp Sensor: "));
  Serial.println(temp_sensor.is_healthy() ? "OK" : "ERROR");
  Serial.print(F("DO Sensor: "));
  Serial.println(do_sensor.is_healthy() ? "OK" : "ERROR");
  Serial.print(F("Level Sensor: "));
  Serial.println(water_level_sensor.is_healthy() ? "OK" : "ERROR");
  Serial.print(F("Turbidity Sensor: "));
  Serial.println(turbidity_sensor.is_healthy() ? "OK" : "ERROR");
  Serial.println();
}

void software_reset() {
  // [수정] WDT를 사용한 하드웨어 리셋 구현
  // 1. 사용자에게 리셋 사실 알림
  Serial.println(F("SYSTEM RESET TRIGGERED by Software Command..."));
  delay(100); // 전송 완료 대기

  // 2. Watchdog Timer 활성화 (최소 시간인 15ms로 설정)
  wdt_enable(WDTO_15MS);

  // 3. 무한 루프로 진입하여 WDT 타임아웃 유발 (15ms 후 하드웨어 리셋 발생)
  while (true) {
    // 아무것도 하지 않음 -> 타임아웃 발생
  }
}
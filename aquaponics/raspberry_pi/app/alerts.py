class AlertSystem:
    def __init__(self, config, db_manager):
        self.config = config
        self.db = db_manager
        # config.json에서 임계값 설정 로드
        self.thresholds = config.get('monitoring', {}).get('alert_thresholds', {})
        
        # [중요] Arduino 데이터 키 -> Config.json 키 매핑 테이블
        # Arduino: "Temp", "Level" / Config: "temperature", "water_level"
        # 나머지는 대소문자까지 정확히 일치해야 함 ("pH", "EC", "DO")
        self.key_map = {
            "pH": "pH",
            "EC": "EC",
            "Temp": "temperature",
            "DO": "DO",
            "Level": "water_level",
            "Turbidity": "turbidity"
        }

    def check_alerts(self, reading):
        if not reading:
            return

        for sensor, value in reading.items():
            # 메타 데이터는 건너뜀
            if sensor in ['timestamp', 'status']: continue
            
            # 1. 키 매핑 (Arduino Key -> Config Key 변환)
            # 매핑 테이블에 없으면 원래 키를 그대로 사용
            config_key = self.key_map.get(sensor, sensor)
            
            # 2. 해당 센서에 대한 임계값 규칙이 있는지 확인
            rules = self.thresholds.get(config_key)
            if not rules: continue

            # 3. 임계값 체크 로직
            # CRITICAL 범위 체크
            if value < rules.get('critical_min', -99999) or value > rules.get('critical_max', 99999):
                self.db.create_alert(
                    sensor_name=sensor, # DB에는 원본 센서 이름 기록
                    alert_type="CRITICAL",
                    value=value,
                    message=f"{sensor} value {value} is CRITICAL (Range: {rules.get('critical_min')}~{rules.get('critical_max')})"
                )
            # WARNING 범위 체크
            elif value < rules.get('min', -99999) or value > rules.get('max', 99999):
                self.db.create_alert(
                    sensor_name=sensor,
                    alert_type="WARNING",
                    value=value,
                    message=f"{sensor} value {value} is out of range (Range: {rules.get('min')}~{rules.get('max')})"
                )
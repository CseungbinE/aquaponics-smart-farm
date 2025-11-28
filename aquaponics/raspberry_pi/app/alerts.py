class AlertSystem:
    def __init__(self, config, db_manager):
        self.config = config
        self.db = db_manager
        self.thresholds = config.get('monitoring', {}).get('alert_thresholds', {})

    def check_alerts(self, reading):
        if not reading:
            return

        for sensor, value in reading.items():
            if sensor in ['timestamp', 'status']: continue
            
            # config.json의 키 이름과 매칭 (대소문자 주의)
            # 아두이노는 "Temp"로 보내지만 config는 "temperature"일 수 있음 -> 매핑 필요
            config_key = sensor.lower()
            if sensor == "Temp": config_key = "temperature"
            if sensor == "Level": config_key = "water_level"
            
            rules = self.thresholds.get(config_key)
            if not rules: continue

            # 임계값 체크
            if value < rules.get('critical_min', -999) or value > rules.get('critical_max', 9999):
                self.db.create_alert(sensor, "CRITICAL", value, f"{sensor} value {value} is critical!")
            elif value < rules.get('min', -999) or value > rules.get('max', 9999):
                self.db.create_alert(sensor, "WARNING", value, f"{sensor} value {value} is out of range.")
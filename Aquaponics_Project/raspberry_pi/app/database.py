import sqlite3
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, config):
        self.db_path = config.get('database', {}).get('path', 'data/aquaponics.db')
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self.get_connection()
        c = conn.cursor()
        
        # 센서 데이터 테이블
        c.execute('''CREATE TABLE IF NOT EXISTS sensor_readings
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TEXT,
                      pH REAL, EC REAL, temperature REAL, 
                      DO REAL, water_level REAL, turbidity REAL,
                      status TEXT)''')

        # 알림 테이블
        c.execute('''CREATE TABLE IF NOT EXISTS alerts
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TEXT,
                      sensor_name TEXT, alert_type TEXT,
                      value REAL, message TEXT,
                      resolved INTEGER DEFAULT 0, resolved_at TEXT)''')
        
        # 캘리브레이션 테이블
        c.execute('''CREATE TABLE IF NOT EXISTS calibrations
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TEXT,
                      sensor_name TEXT,
                      points TEXT)''') # points는 JSON string으로 저장
        conn.commit()
        conn.close()

    def save_reading(self, data):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO sensor_readings 
                     (timestamp, pH, EC, temperature, DO, water_level, turbidity, status)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (datetime.now().isoformat(),
                   data.get('pH'), data.get('EC'), data.get('Temp'),
                   data.get('DO'), data.get('Level'), data.get('Turbidity'),
                   "OK"))
        conn.commit()
        conn.close()

    def get_latest_reading(self):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_history(self, days=1, hours=0, limit=1000):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # 시간 조건 계산
        if hours > 0:
            time_filter = f"datetime('now', '-{hours} hours')"
        else:
            time_filter = f"datetime('now', '-{days} days')"

        c.execute(f"SELECT * FROM sensor_readings WHERE timestamp > {time_filter} ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def create_alert(self, sensor_name, alert_type, value, message):
        conn = self.get_connection()
        c = conn.cursor()
        timestamp = datetime.now().isoformat()
        c.execute("INSERT INTO alerts (timestamp, sensor_name, alert_type, value, message) VALUES (?, ?, ?, ?, ?)",
                  (timestamp, sensor_name, alert_type, value, message))
        alert_id = c.lastrowid
        conn.commit()
        conn.close()
        return {"id": alert_id, "timestamp": timestamp, "message": message}

    def get_active_alerts(self):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM alerts WHERE resolved = 0 ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
        
    # (추가적인 통계, 캘리브레이션 함수 등은 지면 관계상 핵심 로직 위주로 구성했습니다)
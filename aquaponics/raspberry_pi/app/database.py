import sqlite3
import json
from datetime import datetime
import os  # [수정 1] 누락된 os 모듈 추가 (필수)

class DatabaseManager:
    def __init__(self, config):
        self.db_path = config.get('database', {}).get('path', 'data/aquaponics.db')
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_db(self):
        # [수정 1 관련] os 모듈이 있어야 makedirs가 작동함
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

    # [수정 2] 아래부터는 api.py에서 호출하지만 누락되었던 필수 메서드들입니다.

    def get_statistics(self, hours=24):
        """통계 API (/api/statistics)용 메서드"""
        conn = self.get_connection()
        c = conn.cursor()
        time_filter = f"datetime('now', '-{hours} hours')"
        stats = {}
        # pH, EC, temperature, DO, turbidity에 대해 최소/최대/평균 계산
        for col in ['pH', 'EC', 'temperature', 'DO', 'turbidity']:
            c.execute(f"SELECT MIN({col}), MAX({col}), AVG({col}) FROM sensor_readings WHERE timestamp > {time_filter}")
            row = c.fetchone()
            if row and row[0] is not None:
                stats[col] = {"min": row[0], "max": row[1], "avg": round(row[2], 2)}
            else:
                stats[col] = {"min": 0, "max": 0, "avg": 0}
        conn.close()
        return stats

    def resolve_alert(self, alert_id):
        """경고 해결 처리 (/api/alerts/<id>/resolve)"""
        conn = self.get_connection()
        c = conn.cursor()
        timestamp = datetime.now().isoformat()
        c.execute("UPDATE alerts SET resolved = 1, resolved_at = ? WHERE id = ?", (timestamp, alert_id))
        affected = c.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def get_alerts_by_range(self, start_date, end_date):
        """기간별 경고 조회 (/api/alerts)"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM alerts WHERE timestamp BETWEEN ? AND ? ORDER BY id DESC", (start_date, end_date))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def save_calibration(self, sensor_name, data):
        """캘리브레이션 데이터 저장"""
        conn = self.get_connection()
        c = conn.cursor()
        points_json = json.dumps(data.get('points', {}))
        timestamp = datetime.now().isoformat()
        c.execute("INSERT INTO calibrations (timestamp, sensor_name, points) VALUES (?, ?, ?)",
                  (timestamp, sensor_name, points_json))
        conn.commit()
        conn.close()

    def get_latest_calibration(self, sensor_name):
        """최신 캘리브레이션 데이터 조회"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM calibrations WHERE sensor_name = ? ORDER BY id DESC LIMIT 1", (sensor_name,))
        row = c.fetchone()
        conn.close()
        if row:
            res = dict(row)
            try:
                res['points'] = json.loads(res['points'])
            except:
                pass
            return res
        return None
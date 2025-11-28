import threading
import time
from flask import Flask
from app.config import Config
from app.database import DatabaseManager
from app.sensors import SerialSensorManager
from app.alerts import AlertSystem
from app.api import api_bp # 이전에 만든 API 모듈

# --- 전역 객체 초기화 ---
config = Config('../config.json')
db = DatabaseManager(config)
sensors = SerialSensorManager(config)
alerts = AlertSystem(config, db)

app = Flask(__name__)
# API 모듈에서 전역 객체에 접근할 수 있도록 설정에 저장
app.config['SYSTEM_CONFIG'] = config
app.config['DB_MANAGER'] = db

app.register_blueprint(api_bp)

# --- 백그라운드 데이터 수집 스레드 ---
def background_loop():
    interval = config.get('monitoring', {}).get('reading_interval_seconds', 5)
    print("Starting background sensor loop...")
    
    while True:
        try:
            # 1. 아두이노에서 데이터 읽기
            data = sensors.read_all()
            
            if data:
                print(f"Data received: {data}")
                # 2. DB 저장
                db.save_reading(data)
                # 3. 알림 체크
                alerts.check_alerts(data)
            
            time.sleep(interval)
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(5)

# --- 메인 실행 ---
if __name__ == '__main__':
    # 스레드 시작
    t = threading.Thread(target=background_loop, daemon=True)
    t.start()
    
    # 웹 서버 시작
    app.run(host='0.0.0.0', port=5000, debug=False)
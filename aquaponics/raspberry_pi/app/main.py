import threading
import time
import signal
import sys
import logging
from datetime import datetime
from flask import Flask
from app.config import Config
from app.database import DatabaseManager
from app.sensors import SerialSensorManager
from app.alerts import AlertSystem
from app.api import api_bp
from app.dashboard import dashboard_bp

# ==========================================
# 로깅 설정
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("aquaponics.log"), # 파일에 로그 저장
        logging.StreamHandler()                # 콘솔에도 출력
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# 전역 객체 초기화
# ==========================================
# Config 클래스 내부에서 절대 경로를 자동 계산하므로 인자 없이 호출
config = Config() 
db = DatabaseManager(config)
sensors = SerialSensorManager(config)
alerts = AlertSystem(config, db)

# Flask 앱 설정
app = Flask(__name__)
# API 및 다른 모듈에서 접근할 수 있도록 전역 객체 주입
app.config['SYSTEM_CONFIG'] = config
app.config['DB_MANAGER'] = db
app.config['SENSOR_MANAGER'] = sensors  # [추가] 캘리브레이션 명령 전송용

# 블루프린트 등록
app.register_blueprint(api_bp)
app.register_blueprint(dashboard_bp)

# 스레드 제어 플래그
running = True

# ==========================================
# 백그라운드 데이터 수집 루프
# ==========================================
def background_loop():
    logger.info("Starting background sensor data collection loop...")
    
    # 설정에서 주기 가져오기 (기본값 5초)
    interval = config.get('monitoring', {}).get('reading_interval_seconds', 5)
    
    while running:
        try:
            # 1. 아두이노에서 데이터 읽기
            # (SerialSensorManager 내부에서 연결 재시도 로직 포함됨)
            data = sensors.read_all()
            
            if data:
                logger.info(f"Sensor Data Received: {data}")
                
                # 2. 데이터베이스 저장
                try:
                    db.save_reading(data)
                except Exception as db_err:
                    logger.error(f"Database save error: {db_err}")

                # 3. 알림 시스템 체크
                try:
                    alerts.check_alerts(data)
                except Exception as alert_err:
                    logger.error(f"Alert check error: {alert_err}")
            
            # CPU 점유율 방지를 위한 대기
            time.sleep(interval)
            
        except Exception as e:
            logger.error(f"Unexpected error in background loop: {e}")
            time.sleep(5) # 에러 발생 시 잠시 대기 후 재시도

    logger.info("Background loop stopped.")

# ==========================================
# 우아한 종료 처리 (Graceful Shutdown)
# ==========================================
def signal_handler(sig, frame):
    global running
    logger.info("Shutdown signal received. Stopping application...")
    running = False
    if sensors.serial and sensors.serial.is_open:
        sensors.serial.close()
    sys.exit(0)

# ==========================================
# 메인 실행 진입점
# ==========================================
if __name__ == '__main__':
    # 종료 신호(Ctrl+C) 감지 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 데이터 수집 스레드 시작
    sensor_thread = threading.Thread(target=background_loop, daemon=True)
    sensor_thread.start()
    
    # 웹 서버 설정 로드
    web_config = config.get('web_server', {})
    host = web_config.get('host', '0.0.0.0')
    port = web_config.get('port', 5000)
    debug = web_config.get('debug_mode', False)
    
    logger.info(f"Starting Web Server on {host}:{port}")
    
    # Flask 서버 시작 (블로킹 동작)
    # use_reloader=False를 해야 스레드가 중복 실행되지 않음
    app.run(host=host, port=port, debug=debug, use_reloader=False)
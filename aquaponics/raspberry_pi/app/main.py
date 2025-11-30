import threading
import time
import signal
import sys
import logging
from flask import Flask
from app.config import Config
from app.database import DatabaseManager
from app.sensors import SerialSensorManager
from app.alerts import AlertSystem
from app.api import api_bp
from app.dashboard import dashboard_bp  # [추가] 대시보드 모듈 임포트

# ==========================================
# 로깅 설정 (파일 및 콘솔 출력)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("aquaponics.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# 전역 객체 초기화
# ==========================================
# Config 클래스가 절대 경로를 자동 계산하므로 인자 없이 호출
config = Config() 
db = DatabaseManager(config)
sensors = SerialSensorManager(config)
alerts = AlertSystem(config, db)

app = Flask(__name__)
# API 및 블루프린트에서 사용할 수 있도록 전역 객체 주입
app.config['SYSTEM_CONFIG'] = config
app.config['DB_MANAGER'] = db
app.config['SENSOR_MANAGER'] = sensors

# 블루프린트 등록
app.register_blueprint(api_bp)
app.register_blueprint(dashboard_bp)  # [추가] 대시보드 등록

# 스레드 제어 플래그
running = True

# ==========================================
# 백그라운드 데이터 수집 루프
# ==========================================
def background_loop():
    logger.info("Starting background sensor data collection loop...")
    interval = config.get('monitoring', {}).get('reading_interval_seconds', 5)
    
    while running:
        try:
            # 1. 아두이노에서 데이터 읽기
            data = sensors.read_all()
            
            if data:
                logger.info(f"Sensor Data: {data}")
                
                # 2. 데이터베이스 저장
                db.save_reading(data)
                
                # 3. 알림 체크
                alerts.check_alerts(data)
            
            time.sleep(interval)
            
        except Exception as e:
            logger.error(f"Error in background loop: {e}")
            time.sleep(5)

    logger.info("Background loop stopped.")

# ==========================================
# 종료 처리 (Graceful Shutdown)
# ==========================================
def signal_handler(sig, frame):
    global running
    logger.info("Shutdown signal received. Stopping...")
    running = False
    if sensors.serial and sensors.serial.is_open:
        sensors.serial.close()
    sys.exit(0)

# ==========================================
# 메인 실행
# ==========================================
if __name__ == '__main__':
    # Ctrl+C 종료 시그널 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 데이터 수집 스레드 시작
    t = threading.Thread(target=background_loop, daemon=True)
    t.start()
    
    # 웹 서버 설정 로드
    web_config = config.get('web_server', {})
    host = web_config.get('host', '0.0.0.0')
    port = web_config.get('port', 5000)
    debug = web_config.get('debug_mode', False)
    
    logger.info(f"Starting Web Server at http://{host}:{port}")
    
    # Flask 서버 시작 (use_reloader=False는 스레드 중복 실행 방지용)
    app.run(host=host, port=port, debug=debug, use_reloader=False)
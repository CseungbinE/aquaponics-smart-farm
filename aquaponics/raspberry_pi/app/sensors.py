import serial
import json
import time
import logging
import glob

# 로거 설정 (main.py에서 설정된 로거를 상속받음)
logger = logging.getLogger(__name__)

class SerialSensorManager:
    def __init__(self, config):
        self.config = config
        # config.json에서 포트와 보드레이트 가져오기, 없으면 기본값 사용
        # 하드웨어 플랫폼이 'arduino'인 경우에만 유효한 설정
        self.port = config.get('hardware', {}).get('serial_port', '/dev/ttyUSB0') 
        self.baud = config.get('hardware', {}).get('baud_rate', 115200)
        
        # 포트 자동 탐색 시도 (설정된 포트가 없을 경우)
        if not self.port or self.port == 'auto':
             self.port = self.find_arduino_port()

        self.serial = None
        self.connect()

    def find_arduino_port(self):
        """사용 가능한 USB/ACM 포트 자동 탐색"""
        ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        if ports:
            logger.info(f"Auto-detected Arduino port: {ports[0]}")
            return ports[0]
        # 기본값 반환 (연결 시도 시 실패하겠지만)
        logger.warning("No Arduino port auto-detected. Using default /dev/ttyUSB0")
        return '/dev/ttyUSB0'

    def connect(self):
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
                
            self.serial = serial.Serial(self.port, self.baud, timeout=1)
            logger.info(f"Connected to Arduino on {self.port} at {self.baud} baud")
            time.sleep(2) # 아두이노 리셋 대기 (DTR 라인 관련)
        except Exception as e:
            logger.error(f"Serial connection failed on {self.port}: {e}")
            self.serial = None

    def read_all(self):
        # 연결 상태 확인 및 재연결 시도
        if not self.serial or not self.serial.is_open:
            self.connect()
            if not self.serial: # 여전히 연결 실패 시
                return None

        try:
            if self.serial.in_waiting > 0:
                # [수정] 먼저 Raw 바이트 데이터를 읽어옵니다.
                raw_line = self.serial.readline()
                
                try:
                    # [수정] errors='strict'(기본값)를 사용하여 디코딩 시도
                    # 데이터가 깨졌다면 즉시 UnicodeDecodeError 발생
                    line = raw_line.decode('utf-8').strip()
                except UnicodeDecodeError as ue:
                    # [수정] 깨진 데이터는 로그에 남기고 이번 턴은 무시 (데이터 무결성 보장)
                    logger.warning(f"Discarding corrupt serial data: {ue}. Raw hex: {raw_line.hex()}")
                    return None

                # 유효한 JSON 문자열인지 1차 검증
                if line.startswith('{') and line.endswith('}'):
                    try:
                        data = json.loads(line)
                        return data
                    except json.JSONDecodeError as je:
                        logger.warning(f"JSON parse error: {je}. Raw line: {line}")
                        return None
        except serial.SerialException as se:
            logger.error(f"Serial communication error: {se}")
            # 통신 에러 발생 시 연결 끊고 다음 주기 재연결 유도
            if self.serial:
                self.serial.close()
                self.serial = None
        except Exception as e:
            logger.error(f"Unexpected error reading serial: {e}")
        
        return None

    def send_command(self, command):
        """아두이노로 명령 전송 (캘리브레이션 등)"""
        if not self.serial or not self.serial.is_open:
            logger.error("Cannot send command: Serial not connected")
            return False
            
        try:
            # 명령 끝에 개행문자 추가하여 전송
            full_cmd = f"{command}\n"
            self.serial.write(full_cmd.encode('utf-8'))
            logger.info(f"Sent command to Arduino: {command}")
            return True
        except Exception as e:
            logger.error(f"Error sending command '{command}': {e}")
            return False

# [추가] 시뮬레이션용 가짜 센서 매니저
import random

class MockSensorManager:
    def __init__(self, config):
        self.config = config
        logger.info("==========================================")
        logger.info(" RUNNING IN SIMULATION MODE (NO HARDWARE) ")
        logger.info("==========================================")
        
        # 초기값 설정 (정상 범위 내)
        self.current_data = {
            "pH": 7.0,
            "EC": 1400,
            "Temp": 24.0,
            "DO": 6.5,
            "Level": 90.0,
            "Turbidity": 10.0
        }

    def read_all(self):
        # 1. 실제 통신 지연 시뮬레이션
        time.sleep(0.1)
        
        # 2. 랜덤 워크 (Random Walk) 알고리즘으로 데이터가 서서히 변하도록 생성
        # 급격하게 튀지 않고 조금씩 오르내리게 만듦
        self.current_data["pH"] += random.uniform(-0.1, 0.1)
        self.current_data["EC"] += random.uniform(-10, 10)
        self.current_data["Temp"] += random.uniform(-0.2, 0.2)
        self.current_data["DO"] += random.uniform(-0.1, 0.1)
        self.current_data["Level"] += random.uniform(-0.5, 0.5)
        self.current_data["Turbidity"] += random.uniform(-1, 1)

        # 3. 값의 범위 제한 (현실적인 범위로 고정)
        self.current_data["pH"] = round(max(0, min(14, self.current_data["pH"])), 2)
        self.current_data["EC"] = round(max(0, self.current_data["EC"]), 0)
        self.current_data["Temp"] = round(self.current_data["Temp"], 1)
        self.current_data["DO"] = round(max(0, self.current_data["DO"]), 2)
        self.current_data["Level"] = round(max(0, min(100, self.current_data["Level"])), 1)
        self.current_data["Turbidity"] = round(max(0, self.current_data["Turbidity"]), 1)
        
        # 4. 타임스탬프 추가 (JSON 포맷 맞춤)
        result = self.current_data.copy()
        result['timestamp'] = int(time.time())
        
        return result

    def send_command(self, command):
        # 가짜로 명령 받았다고 로그만 출력
        logger.info(f"[SIMULATION] Mock Arduino received command: {command}")
        return True
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
                # readline()은 바이트열을 반환, decode()로 문자열 변환
                # strip()으로 앞뒤 공백 및 개행문자 제거
                line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                
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
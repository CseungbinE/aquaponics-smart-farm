import serial
import json
import time
import logging

class SerialSensorManager:
    def __init__(self, config):
        self.port = '/dev/ttyUSB0' # 아두이노 연결 포트 (환경에 따라 수정 필요)
        self.baud = 115200
        self.serial = None
        self.connect()

    def connect(self):
        try:
            self.serial = serial.Serial(self.port, self.baud, timeout=1)
            print(f"Connected to Arduino on {self.port}")
            time.sleep(2) # 아두이노 리셋 대기
        except Exception as e:
            print(f"Serial connection failed: {e}")

    def read_all(self):
        if not self.serial or not self.serial.is_open:
            self.connect()
            return None

        try:
            if self.serial.in_waiting > 0:
                line = self.serial.readline().decode('utf-8').strip()
                # 아두이노가 보내는 JSON 문자열 파싱
                # 예: {"timestamp":123, "pH":6.8, ...}
                if line.startswith('{') and line.endswith('}'):
                    return json.loads(line)
        except Exception as e:
            print(f"Error reading serial: {e}")
        
        return None
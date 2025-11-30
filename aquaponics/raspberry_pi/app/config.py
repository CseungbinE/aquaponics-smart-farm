import json
import os

class Config:
    def __init__(self, config_path=None):
        # 기본값: 현재 파일(config.py) 기준 상위상위 폴더의 config.json
        # 구조: aquaponics/config.json
        #       aquaponics/raspberry_pi/app/config.py
        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, 'config.json')
            
        self.config_path = config_path
        self.config_data = {}
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.config_data = json.load(f)
                print(f"Loaded config from {self.config_path}")
            except json.JSONDecodeError as e:
                print(f"Error parsing config file: {e}")
        else:
            print(f"Warning: Config file not found at {self.config_path}")
            # 기본 빈 설정이라도 생성하여 에러 방지
            self.config_data = {}

    def get(self, key, default=None):
        return self.config_data.get(key, default)

    def update(self, new_data):
        # 재귀적 업데이트 로직이 필요할 수 있으나 여기선 간단히 최상위 키 병합
        self.config_data.update(new_data)

    def save(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config_data, f, indent=2)
            print(f"Config saved to {self.config_path}")
        except Exception as e:
            print(f"Error saving config: {e}")
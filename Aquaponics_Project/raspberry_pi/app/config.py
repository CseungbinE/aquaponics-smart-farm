import json
import os

class Config:
    def __init__(self, config_path='../config.json'):
        self.config_path = config_path
        self.config_data = {}
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.config_data = json.load(f)
        else:
            print(f"Warning: Config file not found at {self.config_path}")

    def get(self, key, default=None):
        return self.config_data.get(key, default)

    def update(self, new_data):
        # 재귀적 업데이트 로직이 필요할 수 있으나 여기선 간단히 최상위 키 병합
        self.config_data.update(new_data)

    def save(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config_data, f, indent=2)
import yaml
import os

class ConfigManager:
    def __init__(self, config_path="config/default.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.callbacks = []

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def load_config(self):
        if not os.path.exists(self.config_path):
            return {}
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def set(self, key, value):
        keys = key.split('.')
        target = self.config
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = value
        
        # Notify callbacks
        for callback in self.callbacks:
            callback(key, value)

    def save(self):
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f)
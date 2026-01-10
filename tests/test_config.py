import unittest
import os
import yaml
from config.manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.config_path = "test_config.yaml"
        self.default_config = {
            'audio': {'input_type': 'microphone'},
            'visualizer': {'fps': 30}
        }
        with open(self.config_path, 'w') as f:
            yaml.dump(self.default_config, f)
        self.manager = ConfigManager(self.config_path)

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_get(self):
        self.assertEqual(self.manager.get('audio.input_type'), 'microphone')
        self.assertEqual(self.manager.get('visualizer.fps'), 30)
        self.assertEqual(self.manager.get('non.existent', 'default'), 'default')

    def test_set(self):
        self.manager.set('audio.input_type', 'file')
        self.assertEqual(self.manager.get('audio.input_type'), 'file')
        
        self.manager.set('new.key', 123)
        self.assertEqual(self.manager.get('new.key'), 123)

    def test_save(self):
        self.manager.set('audio.input_type', 'file')
        self.manager.save()
        
        with open(self.config_path, 'r') as f:
            saved_config = yaml.safe_load(f)
        self.assertEqual(saved_config['audio']['input_type'], 'file')

if __name__ == '__main__':
    unittest.main()

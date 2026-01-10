import unittest
import numpy as np
from audio.processor import AudioProcessor
from config.manager import ConfigManager
import os

class TestAudioProcessor(unittest.TestCase):
    def setUp(self):
        # Create a dummy config
        self.config_path = "test_config.yaml"
        with open(self.config_path, 'w') as f:
            f.write("audio:\n  sample_rate: 44100\nvisualizer:\n  fft_size: 1024\n  frequency_range: [20, 20000]\n")
        self.config_manager = ConfigManager(self.config_path)
        self.processor = AudioProcessor(self.config_manager)

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_apply_transformations_volume(self):
        data = np.array([1000, 2000, 3000], dtype=np.int16)
        self.config_manager.set('processing.volume', 0.5)
        processed = self.processor.apply_transformations(data)
        np.testing.assert_array_equal(processed, [500, 1000, 1500])

    def test_process_fft(self):
        # Generate a 440Hz sine wave
        duration = 0.1
        t = np.linspace(0, duration, int(44100 * duration), endpoint=False)
        data = (np.sin(2 * np.pi * 440 * t) * 10000).astype(np.int16)
        
        magnitudes, frequencies = self.processor.process_fft(data)
        
        # Find peak frequency
        peak_freq = frequencies[np.argmax(magnitudes)]
        self.assertAlmostEqual(peak_freq, 440, delta=20)

    def test_get_bars(self):
        magnitudes = np.random.rand(512)
        frequencies = np.linspace(0, 22050, 512)
        bars = self.processor.get_bars(magnitudes, frequencies, num_bars=10)
        self.assertEqual(len(bars), 10)

    def test_multi_channel_fft(self):
        self.config_manager.set('audio.channels', 2)
        self.processor = AudioProcessor(self.config_manager)
        
        # Interleaved stereo data: [L, R, L, R, ...]
        data = np.array([1000, -1000, 2000, -2000, 3000, -3000], dtype=np.int16)
        magnitudes, frequencies = self.processor.process_fft(data)
        
        self.assertEqual(len(magnitudes), 2)
        self.assertEqual(len(magnitudes[0]), len(magnitudes[1]))
        
        bars = self.processor.get_bars(magnitudes, frequencies, num_bars=5)
        self.assertEqual(len(bars), 2)
        self.assertEqual(len(bars[0]), 5)

if __name__ == '__main__':
    unittest.main()

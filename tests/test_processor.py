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
        self.config_manager.set('processing.lpf_cutoff', 22050.0)
        self.config_manager.set('processing.hpf_cutoff', 0.0)
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

    def test_multi_channel_transformations(self):
        self.config_manager.set('audio.channels', 2)
        self.processor = AudioProcessor(self.config_manager)
        
        # Interleaved stereo: [L1, R1, L2, R2]
        data = np.array([1000, 2000, 3000, 4000], dtype=np.int16)
        
        # Test Volume
        self.config_manager.set('processing.volume', 0.5)
        self.config_manager.set('processing.lpf_cutoff', 22050.0)
        self.config_manager.set('processing.hpf_cutoff', 0.0)
        processed = self.processor.apply_transformations(data)
        np.testing.assert_array_equal(processed, [500, 1000, 1500, 2000])
        
        # Test Pitch Shift (should handle channels independently)
        self.config_manager.set('processing.pitch', 2.0)
        self.config_manager.set('processing.volume', 1.0)
        processed = self.processor.apply_transformations(data)
        # num_samples per channel is 2. pitch 2.0 means we get 1 sample per channel.
        # Should be [L1, R1]
        self.assertEqual(len(processed), 2)
        np.testing.assert_array_equal(processed, [1000, 2000])

    def test_filters(self):
        # Generate a signal with 100Hz and 10000Hz components
        fs = 44100
        duration = 0.5
        t = np.linspace(0, duration, int(fs * duration), endpoint=False)
        low_freq = 100
        high_freq = 10000
        data = (np.sin(2 * np.pi * low_freq * t) * 5000 + np.sin(2 * np.pi * high_freq * t) * 5000).astype(np.int16)
        
        # Test LPF at 1000Hz (should remove high_freq)
        self.config_manager.set('processing.lpf_cutoff', 1000.0)
        self.config_manager.set('processing.hpf_cutoff', 0.0)
        self.processor = AudioProcessor(self.config_manager) # Reset
        processed_lpf = self.processor.apply_transformations(data)
        
        # Check FFT of LPF signal
        m_lpf, f_lpf = self.processor.process_fft(processed_lpf)
        # Find magnitudes at low and high freqs
        low_idx = np.argmin(np.abs(f_lpf - low_freq))
        high_idx = np.argmin(np.abs(f_lpf - high_freq))
        
        self.assertGreater(m_lpf[low_idx], m_lpf[high_idx] * 10) # Low freq should be much stronger than high freq
        
        # Test HPF at 5000Hz (should remove low_freq)
        self.config_manager.set('processing.lpf_cutoff', 22050.0)
        self.config_manager.set('processing.hpf_cutoff', 5000.0)
        self.processor = AudioProcessor(self.config_manager) # Reset
        processed_hpf = self.processor.apply_transformations(data)
        
        # Check FFT of HPF signal
        m_hpf, f_hpf = self.processor.process_fft(processed_hpf)
        low_idx = np.argmin(np.abs(f_hpf - low_freq))
        high_idx = np.argmin(np.abs(f_hpf - high_freq))
        
        self.assertGreater(m_hpf[high_idx], m_hpf[low_idx] * 10) # High freq should be much stronger than low freq

if __name__ == '__main__':
    unittest.main()

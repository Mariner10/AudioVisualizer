import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from audio.processor import AudioProcessor
from config.manager import ConfigManager

def test_fft():
    config = ConfigManager()
    processor = AudioProcessor(config)
    
    # Generate a 440Hz sine wave
    fs = 44100
    duration = 1.0
    f = 440
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    data = (np.sin(2 * np.pi * f * t) * 32767).astype(np.int16)
    
    # Process a chunk
    chunk = data[:1024]
    magnitudes, frequencies = processor.process_fft(chunk)
    
    # Peak frequency should be around 440Hz
    peak_freq = frequencies[np.argmax(magnitudes)]
    print(f"Peak frequency: {peak_freq} Hz")
    
    assert abs(peak_freq - 440) < 50
    print("FFT Test Passed!")

if __name__ == "__main__":
    test_fft()

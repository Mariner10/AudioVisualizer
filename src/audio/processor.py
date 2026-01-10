import numpy as np
from scipy.fft import rfft, rfftfreq

class AudioProcessor:
    def __init__(self, config):
        self.config = config
        self.sample_rate = config.get('audio.sample_rate', 44100)
        self.fft_size = config.get('visualizer.fft_size', 1024)
        self.freq_range = config.get('visualizer.frequency_range', [20, 20000])

    def process_fft(self, data):
        """
        Perform FFT on the audio data.
        data: numpy array (int16)
        returns: magnitudes, frequencies
        """
        # Windowing to reduce spectral leakage
        window = np.hanning(len(data))
        windowed_data = data * window
        
        # Perform real FFT
        fft_data = rfft(windowed_data)
        magnitudes = np.abs(fft_data)
        frequencies = rfftfreq(len(data), 1 / self.sample_rate)
        
        # Filter by frequency range
        mask = (frequencies >= self.freq_range[0]) & (frequencies <= self.freq_range[1])
        return magnitudes[mask], frequencies[mask]

    def get_bars(self, magnitudes, frequencies, num_bars=64):
        """
        Group FFT results into bars for visualization.
        """
        if len(magnitudes) == 0:
            return np.zeros(num_bars)
            
        # Logarithmic scaling for bars is often better for audio
        indices = np.round(np.logspace(0, np.log10(len(magnitudes)-1), num_bars+1)).astype(int)
        bars = []
        for i in range(num_bars):
            start, end = indices[i], indices[i+1]
            if start == end:
                val = magnitudes[start]
            else:
                val = np.mean(magnitudes[start:end])
            bars.append(val)
            
        return np.array(bars)

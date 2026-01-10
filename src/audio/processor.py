import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.interpolate import interp1d

class AudioProcessor:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.sample_rate = config_manager.get('audio.sample_rate', 44100)
        self.fft_size = config_manager.get('visualizer.fft_size', 1024)
        self.freq_range = config_manager.get('visualizer.frequency_range', [20, 20000])
        self.channels = config_manager.get('audio.channels', 1)

    def apply_transformations(self, data):
...
        # Clip and convert back to int16
        return np.clip(audio_float, -32768, 32767).astype(np.int16)

    def process_fft(self, data):
        """
        Perform FFT on the audio data.
        data: numpy array (int16)
        returns: magnitudes, frequencies (or list of magnitudes if multi-channel)
        """
        if len(data) == 0:
            return np.array([]), np.array([])
            
        if self.channels == 1:
            return self._fft_mono(data)
        else:
            # Process each channel separately
            mags = []
            freqs = None
            for i in range(self.channels):
                m, f = self._fft_mono(data[i::self.channels])
                mags.append(m)
                freqs = f
            return mags, freqs

    def _fft_mono(self, data):
        # Windowing to reduce spectral leakage
        window = np.hanning(len(data))
        windowed_data = data.astype(np.float32) * window
        
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
        if isinstance(magnitudes, list):
            # Handle multi-channel
            return [self._get_bars_mono(m, frequencies, num_bars) for m in magnitudes]
        return self._get_bars_mono(magnitudes, frequencies, num_bars)

    def _get_bars_mono(self, magnitudes, frequencies, num_bars=64):
        if len(magnitudes) == 0:
            return np.zeros(num_bars)
            
        # Logarithmic scaling for bars
        # Avoid log(0)
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

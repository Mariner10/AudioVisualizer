import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.interpolate import interp1d

class AudioProcessor:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.sample_rate = config_manager.get('audio.sample_rate', 44100)
        self.fft_size = config_manager.get('visualizer.fft_size', 1024)
        self.freq_range = config_manager.get('visualizer.frequency_range', [20, 20000])

    def apply_transformations(self, data):
        """
        Apply volume, pitch, and timescale transformations to the audio data.
        data: numpy array (int16)
        returns: transformed numpy array (int16)
        """
        volume = self.config_manager.get('processing.volume', 1.0)
        pitch = self.config_manager.get('processing.pitch', 1.0)
        
        # Convert to float for processing
        audio_float = data.astype(np.float32)
        
        # Apply Pitch Shifting (simple resampling)
        if pitch != 1.0:
            indices = np.arange(0, len(audio_float), pitch)
            indices = indices[indices < len(audio_float)]
            if len(indices) > 0:
                f = interp1d(np.arange(len(audio_float)), audio_float, kind='linear', fill_value="extrapolate")
                audio_float = f(indices)
                # Rescale back to original length to maintain chunk size? 
                # Actually, for real-time it's better to maintain sample rate.
                # If we pitch up, we have fewer samples. If we pitch down, we have more.
                # This affects timescale too.
        
        # Apply Volume
        if volume != 1.0:
            audio_float *= volume
            
        # Clip and convert back to int16
        return np.clip(audio_float, -32768, 32767).astype(np.int16)

    def process_fft(self, data):
        """
        Perform FFT on the audio data.
        data: numpy array (int16)
        returns: magnitudes, frequencies
        """
        if len(data) == 0:
            return np.array([]), np.array([])
            
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

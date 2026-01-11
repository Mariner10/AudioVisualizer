import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.interpolate import interp1d
from scipy import signal

class AudioProcessor:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.sample_rate = config_manager.get('audio.sample_rate', 44100)
        self.fft_size = config_manager.get('visualizer.fft_size', 1024)
        self.freq_range = config_manager.get('visualizer.frequency_range', [20, 20000])
        self.channels = config_manager.get('audio.channels', 1)
        self.modulation_phase = 0.0
        
        # Filter states
        self.lpf_zi = None
        self.hpf_zi = None
        self.last_lpf_cutoff = None
        self.last_hpf_cutoff = None
        
        # FFT Caching
        self.cached_window = None
        self.cached_frequencies = None
        self.last_fft_len = 0

    def apply_transformations(self, data):
        """
        Apply volume, pitch, timescale, and modulation transformations.
        """
        volume = self.config_manager.get('processing.volume', 1.0)
        pitch = self.config_manager.get('processing.pitch', 1.0)
        modulation_freq = self.config_manager.get('processing.modulation_freq', 0.0)
        modulation_type = self.config_manager.get('processing.modulation_type', 'ring')
        
        # Convert to float for processing
        audio_float = data.astype(np.float32)
        
        # Reshape if multi-channel
        if self.channels > 1:
            audio_float = audio_float.reshape(-1, self.channels)
        
        # Apply Pitch Shifting (simple resampling)
        if pitch != 1.0 and pitch > 0:
            num_samples = len(audio_float)
            old_indices = np.arange(num_samples)
            new_indices = np.arange(0, num_samples, pitch)
            
            if self.channels > 1:
                # Interp each channel separately
                new_audio = np.zeros((len(new_indices), self.channels), dtype=np.float32)
                for i in range(self.channels):
                    new_audio[:, i] = np.interp(new_indices, old_indices, audio_float[:, i])
                audio_float = new_audio
            else:
                audio_float = np.interp(new_indices, old_indices, audio_float)
        
        # Apply Modulation
        if modulation_freq > 0:
            num_samples = len(audio_float)
            # Maintain phase to avoid clicks
            t = np.arange(num_samples) / self.sample_rate
            phase_step = 2 * np.pi * modulation_freq
            carrier = np.sin(self.modulation_phase + phase_step * t)
            self.modulation_phase = (self.modulation_phase + phase_step * num_samples / self.sample_rate) % (2 * np.pi)
            
            if self.channels > 1:
                carrier = carrier.reshape(-1, 1) # Broadcast across channels
            
            if modulation_type == 'am':
                audio_float = audio_float * (0.5 + 0.5 * carrier)
            else: # 'ring'
                audio_float *= carrier
        else:
            self.modulation_phase = 0.0 # Reset phase if modulation is off

        # Apply Filters
        lpf_cutoff = self.config_manager.get('processing.lpf_cutoff', 20000.0)
        hpf_cutoff = self.config_manager.get('processing.hpf_cutoff', 0.0)

        # Low Pass Filter
        if lpf_cutoff < self.sample_rate / 2:
            if lpf_cutoff != self.last_lpf_cutoff:
                # Design filter
                b, a = signal.butter(4, lpf_cutoff, btype='low', fs=self.sample_rate)
                self.lpf_b, self.lpf_a = b, a
                # Initialize zi for all channels
                self.lpf_zi = signal.lfilter_zi(b, a)
                if self.channels > 1:
                    self.lpf_zi = np.tile(self.lpf_zi, (self.channels, 1)).T
                self.last_lpf_cutoff = lpf_cutoff
            
            audio_float, self.lpf_zi = signal.lfilter(self.lpf_b, self.lpf_a, audio_float, axis=0, zi=self.lpf_zi)

        # High Pass Filter
        if hpf_cutoff > 0:
            if hpf_cutoff != self.last_hpf_cutoff:
                # Design filter
                b, a = signal.butter(4, hpf_cutoff, btype='high', fs=self.sample_rate)
                self.hpf_b, self.hpf_a = b, a
                # Initialize zi for all channels
                self.hpf_zi = signal.lfilter_zi(b, a)
                if self.channels > 1:
                    self.hpf_zi = np.tile(self.hpf_zi, (self.channels, 1)).T
                self.last_hpf_cutoff = hpf_cutoff
            
            audio_float, self.hpf_zi = signal.lfilter(self.hpf_b, self.hpf_a, audio_float, axis=0, zi=self.hpf_zi)
        
        # Apply Volume
        if volume != 1.0:
            audio_float *= volume
            
        # Flatten back if multi-channel
        if self.channels > 1:
            audio_float = audio_float.flatten()
            
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
        if len(data) < 2:
            return np.array([]), np.array([])
            
        # Cache window and frequencies if length changed
        if len(data) != self.last_fft_len:
            self.cached_window = np.hanning(len(data))
            self.cached_frequencies = rfftfreq(len(data), 1 / self.sample_rate)
            self.last_fft_len = len(data)
            
        # Windowing to reduce spectral leakage
        windowed_data = data.astype(np.float32) * self.cached_window
        
        # Perform real FFT
        fft_data = rfft(windowed_data)
        magnitudes = np.abs(fft_data)
        
        # Filter by frequency range
        mask = (self.cached_frequencies >= self.freq_range[0]) & (self.cached_frequencies <= self.freq_range[1])
        return magnitudes[mask], self.cached_frequencies[mask]

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
        if len(magnitudes) < 2:
             return np.full(num_bars, magnitudes[0] if len(magnitudes) > 0 else 0)
             
        indices = np.round(np.logspace(0, np.log10(len(magnitudes)-1), num_bars+1)).astype(int)
        bars = []
        for i in range(num_bars):
            start, end = indices[i], indices[i+1]
            if start == end:
                val = magnitudes[start] if start < len(magnitudes) else 0
            else:
                val = np.mean(magnitudes[start:end])
            bars.append(val)
            
        return np.array(bars)
import pyaudio
import numpy as np
import threading
import time
from pydub import AudioSegment
import io

class AudioInput:
    def __init__(self, config):
        self.config = config
        self.chunk_size = config.get('audio.chunk_size', 1024)
        self.sample_rate = config.get('audio.sample_rate', 44100)
        self.channels = config.get('audio.channels', 1)
        self.running = False
        self.stream = None
        self.p = pyaudio.PyAudio()
        self.callbacks = []

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def _notify_callbacks(self, data):
        for callback in self.callbacks:
            callback(data)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

    def _run(self):
        raise NotImplementedError

class MicrophoneInput(AudioInput):
    def _run(self):
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        while self.running:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                # Convert bytes to numpy array
                audio_data = np.frombuffer(data, dtype=np.int16)
                self._notify_callbacks(audio_data)
            except Exception as e:
                print(f"Error reading microphone: {e}")
                break

class FileInput(AudioInput):
    def __init__(self, config):
        super().__init__(config)
        self.file_path = config.get('audio.file_path')
        self.audio_segment = None
        
    def _run(self):
        if not self.file_path:
            print("No file path provided")
            return

        # Load audio file using pydub
        try:
            audio = AudioSegment.from_file(self.file_path)
            audio = audio.set_frame_rate(self.sample_rate).set_channels(self.channels)
            self.audio_segment = audio
        except Exception as e:
            print(f"Error loading file {self.file_path}: {e}")
            return

        # Convert to raw data
        raw_data = np.array(self.audio_segment.get_array_of_samples())
        
        # We'll use a pointer to allow variable read sizes if needed in future
        # For now, still read chunk_size but adjust sleep
        i = 0
        while i < len(raw_data) and self.running:
            # Get current settings
            timescale = self.config.get('processing.timescale', 1.0)
            pitch = self.config.get('processing.pitch', 1.0)
            if timescale <= 0: timescale = 1.0
            if pitch <= 0: pitch = 1.0
            
            chunk = raw_data[i:i + self.chunk_size]
            if len(chunk) < self.chunk_size:
                chunk = np.pad(chunk, (0, self.chunk_size - len(chunk)))
            
            self._notify_callbacks(chunk)
            i += self.chunk_size
            
            # The duration of the processed chunk (after pitch shifting) is:
            # (chunk_size / pitch) / sample_rate
            # And we want to scale that by 1/timescale for speed
            actual_duration = (len(chunk) / (pitch * self.channels)) / self.sample_rate
            sleep_time = actual_duration / timescale
            
            # Since notify_callbacks might take some time, we should ideally
            # subtract the elapsed time, but for now simple sleep is improved
            time.sleep(max(0, sleep_time))

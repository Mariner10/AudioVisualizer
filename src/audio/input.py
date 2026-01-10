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
        
        # Calculate delay for real-time playback simulation
        delay = self.chunk_size / self.sample_rate

        for i in range(0, len(raw_data), self.chunk_size):
            if not self.running:
                break
            
            chunk = raw_data[i:i + self.chunk_size]
            if len(chunk) < self.chunk_size:
                # Pad with zeros if last chunk is small
                chunk = np.pad(chunk, (0, self.chunk_size - len(chunk)))
            
            self._notify_callbacks(chunk)
            time.sleep(delay)

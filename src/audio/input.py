import pyaudio
import numpy as np
import threading
import time
from pydub import AudioSegment
import io
import os
from utils.logger import logger

class AudioInput:
    def __init__(self, config):
        self.config = config
        self.chunk_size = config.get('audio.chunk_size', 1024)
        self.sample_rate = config.get('audio.sample_rate', 44100)
        self.channels = config.get('audio.channels', 1)
        self.running = False
        self.stream = None
        try:
            self.p = pyaudio.PyAudio()
        except Exception as e:
            logger.error(f"Failed to initialize PyAudio: {e}")
            self.p = None
        self.callbacks = []
        self.thread = None

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def _notify_callbacks(self, data):
        for callback in self.callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in audio callback: {e}")

    def start(self):
        if self.running:
            return
        logger.info(f"Starting {self.__class__.__name__}")
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        if not self.running:
            return
        logger.info(f"Stopping {self.__class__.__name__}")
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error closing stream: {e}")
        if self.p:
            try:
                self.p.terminate()
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")

    def _run(self):
        raise NotImplementedError

class MicrophoneInput(AudioInput):
    def _run(self):
        if not self.p:
            logger.error("PyAudio not initialized, cannot start microphone input")
            self.running = False
            return

        try:
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
        except Exception as e:
            logger.error(f"Failed to open microphone stream: {e}")
            self.running = False
            return

        logger.info("Microphone stream opened successfully")
        while self.running:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                self._notify_callbacks(audio_data)
            except Exception as e:
                logger.error(f"Error reading from microphone: {e}")
                time.sleep(0.1) # Avoid tight loop on error
                
class FileInput(AudioInput):
    def __init__(self, config):
        super().__init__(config)
        self.file_path = config.get('audio.file_path')
        self.audio_segment = None
        
    def _run(self):
        if not self.file_path:
            logger.error("No file path provided for FileInput")
            self.running = False
            return

        if not os.path.exists(self.file_path):
            logger.error(f"File not found: {self.file_path}")
            self.running = False
            return

        logger.info(f"Loading audio file: {self.file_path}")
        try:
            audio = AudioSegment.from_file(self.file_path)
            audio = audio.set_frame_rate(self.sample_rate).set_channels(self.channels)
            self.audio_segment = audio
        except Exception as e:
            logger.error(f"Error loading file {self.file_path}: {e}")
            self.running = False
            return

        # Convert to raw data
        raw_data = np.array(self.audio_segment.get_array_of_samples())
        num_samples = len(raw_data)
        logger.info(f"File loaded successfully, {num_samples} samples")
        
        i = 0
        while i < num_samples and self.running:
            timescale = self.config.get('processing.timescale', 1.0)
            pitch = self.config.get('processing.pitch', 1.0)
            if timescale <= 0: timescale = 1.0
            if pitch <= 0: pitch = 1.0
            
            chunk = raw_data[i:i + self.chunk_size]
            if len(chunk) < self.chunk_size:
                chunk = np.pad(chunk, (0, self.chunk_size - len(chunk)))
            
            self._notify_callbacks(chunk)
            i += self.chunk_size
            
            actual_duration = (len(chunk) / (pitch * self.channels)) / self.sample_rate
            sleep_time = actual_duration / timescale
            time.sleep(max(0, sleep_time))
            
        if i >= num_samples:
            logger.info("Reached end of audio file")
            self.running = False


import pyaudio
import numpy as np
from utils.logger import logger

class AudioOutput:
    def __init__(self, config):
        self.config = config
        self.sample_rate = config.get('audio.sample_rate', 44100)
        self.channels = config.get('audio.channels', 1)
        self.chunk_size = config.get('audio.chunk_size', 1024)
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size
            )
            logger.info("Audio output stream opened successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AudioOutput: {e}")
            self.p = None
            self.stream = None

    def play(self, data):
        """
        Play a chunk of audio data.
        data: numpy array (int16)
        """
        if not self.stream:
            return
            
        try:
            self.stream.write(data.tobytes())
        except Exception as e:
            logger.error(f"Error writing to audio output stream: {e}")

    def stop(self):
        logger.info("Stopping AudioOutput")
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error closing output stream: {e}")
        if self.p:
            try:
                self.p.terminate()
            except Exception as e:
                logger.error(f"Error terminating PyAudio in AudioOutput: {e}")


import pyaudio
import numpy as np

class AudioOutput:
    def __init__(self, config):
        self.config = config
        self.sample_rate = config.get('audio.sample_rate', 44100)
        self.channels = config.get('audio.channels', 1)
        self.chunk_size = config.get('audio.chunk_size', 1024)
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            frames_per_buffer=self.chunk_size
        )

    def play(self, data):
        """
        Play a chunk of audio data.
        data: numpy array (int16)
        """
        self.stream.write(data.tobytes())

    def stop(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

import wave
import os
import time

class AudioRecorder:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.recording = False
        self.wave_file = None
        self.file_path = None

    def start(self):
        if self.recording:
            return
            
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        self.file_path = f"recordings/recording_{timestamp}.wav"
        
        # Ensure recordings directory exists
        os.makedirs("recordings", exist_ok=True)
        
        sample_rate = self.config_manager.get('audio.sample_rate', 44100)
        channels = self.config_manager.get('audio.channels', 1)
        
        self.wave_file = wave.open(self.file_path, 'wb')
        self.wave_file.setnchannels(channels)
        self.wave_file.setsampwidth(2) # 16-bit
        self.wave_file.setframerate(sample_rate)
        
        self.recording = True
        print(f"Started recording to {self.file_path}")

    def stop(self):
        if not self.recording:
            return
            
        self.recording = False
        if self.wave_file:
            self.wave_file.close()
            self.wave_file = None
        print(f"Stopped recording. Saved to {self.file_path}")

    def write(self, data):
        if self.recording and self.wave_file:
            self.wave_file.writeframes(data.tobytes())

    def toggle(self):
        if self.recording:
            self.stop()
        else:
            self.start()

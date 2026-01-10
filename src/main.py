import sys
import os
import signal
import time
from config.manager import ConfigManager
from audio.input import MicrophoneInput, FileInput
from audio.output import AudioOutput
from audio.processor import AudioProcessor
from visualizer.terminal import TerminalVisualizer

class AudioVisualizerApp:
    def __init__(self, config_path="config/default.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        
        self.processor = AudioProcessor(self.config_manager)
        self.output = AudioOutput(self.config_manager)
        self.visualizer = TerminalVisualizer(self.config_manager)
        
        input_type = self.config_manager.get('audio.input_type', 'microphone')
        if input_type == 'file':
            self.input = FileInput(self.config_manager)
        else:
            self.input = MicrophoneInput(self.config_manager)
            
        self.input.register_callback(self.audio_callback)
        self.running = False

    def audio_callback(self, data):
        # Play audio back
        self.output.play(data)
        
        # Process FFT
        magnitudes, frequencies = self.processor.process_fft(data)
        
        # Get bars for visualization
        bars = self.processor.get_bars(magnitudes, frequencies, num_bars=self.visualizer.width)
        
        # Render in terminal
        display_type = self.config_manager.get('terminal.display_type', 'bar')
        if display_type == 'braille':
            self.visualizer.render_braille(bars)
        else:
            self.visualizer.render_bars(bars)

    def start(self):
        print("Starting AudioVisualizer...")
        self.running = True
        self.input.start()
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        print("Stopping AudioVisualizer...")
        self.running = False
        self.input.stop()
        self.output.stop()

if __name__ == "__main__":
    app = AudioVisualizerApp()
    app.start()

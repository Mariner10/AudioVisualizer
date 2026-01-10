import sys
import os
import signal
import time
from config.manager import ConfigManager
from audio.input import MicrophoneInput, FileInput
from audio.output import AudioOutput
from audio.processor import AudioProcessor
from visualizer.terminal import TerminalVisualizer
from visualizer.server import VisualizerServer

class AudioVisualizerApp:
    def __init__(self, config_path="config/default.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        
        self.processor = AudioProcessor(self.config_manager)
        self.output = AudioOutput(self.config_manager)
        self.terminal_visualizer = TerminalVisualizer(self.config_manager)
        self.server = VisualizerServer(self.config_manager)
        
        input_type = self.config_manager.get('audio.input_type', 'microphone')
        if input_type == 'file':
            self.input = FileInput(self.config_manager)
        else:
            self.input = MicrophoneInput(self.config_manager)
            
        self.input.register_callback(self.audio_callback)
        self.running = False

    def audio_callback(self, data):
        # Apply transformations (volume, pitch, etc.)
        processed_data = self.processor.apply_transformations(data)
        
        # Play audio back
        self.output.play(processed_data)
        
        # Process FFT
        magnitudes, frequencies = self.processor.process_fft(processed_data)
        
        # Get bars for visualization
        num_bars = self.config_manager.get('visualizer.num_bars', 64)
        bars = self.processor.get_bars(magnitudes, frequencies, num_bars=num_bars)
        
        # Send to browser
        self.server.send_data(bars)
        
        # Render in terminal if enabled
        if self.config_manager.get('visualizer.type') == 'terminal':
            display_type = self.config_manager.get('terminal.display_type', 'bar')
            if display_type == 'braille':
                self.terminal_visualizer.render_braille(bars)
            else:
                self.terminal_visualizer.render_bars(bars)

    def start(self):
        print("Starting AudioVisualizer...")
        self.running = True
        self.server.start()
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

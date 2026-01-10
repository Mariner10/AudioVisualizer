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
from utils.keyboard import KeyboardHandler

class AudioVisualizerApp:
    def __init__(self, config_path="config/default.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        
        self.processor = AudioProcessor(self.config_manager)
        self.output = AudioOutput(self.config_manager)
        self.terminal_visualizer = TerminalVisualizer(self.config_manager)
        self.server = VisualizerServer(self.config_manager)
        self.keyboard = KeyboardHandler(self.handle_key)
        
        input_type = self.config_manager.get('audio.input_type', 'microphone')
        if input_type == 'file':
            self.input = FileInput(self.config_manager)
        else:
            self.input = MicrophoneInput(self.config_manager)
            
        self.input.register_callback(self.audio_callback)
        self.running = False
        self.show_menu = False

    def handle_key(self, char):
        if char == 'q':
            self.stop()
            sys.exit(0)
        elif char == '+':
            vol = self.config_manager.get('processing.volume', 1.0)
            self.config_manager.set('processing.volume', min(2.0, vol + 0.1))
        elif char == '-':
            vol = self.config_manager.get('processing.volume', 1.0)
            self.config_manager.set('processing.volume', max(0.0, vol - 0.1))
        elif char == ']':
            pitch = self.config_manager.get('processing.pitch', 1.0)
            self.config_manager.set('processing.pitch', min(2.0, pitch + 0.1))
        elif char == '[':
            pitch = self.config_manager.get('processing.pitch', 1.0)
            self.config_manager.set('processing.pitch', max(0.5, pitch - 0.1))
        elif char == 't':
            types = ['bar', 'braille', 'line', 'bi-directional']
            current = self.config_manager.get('terminal.display_type', 'bar')
            new_idx = (types.index(current) + 1) % len(types) if current in types else 0
            self.config_manager.set('terminal.display_type', types[new_idx])
        elif char == 'l':
            ts = self.config_manager.get('processing.timescale', 1.0)
            self.config_manager.set('processing.timescale', min(2.0, ts + 0.1))
        elif char == 'k':
            ts = self.config_manager.get('processing.timescale', 1.0)
            self.config_manager.set('processing.timescale', max(0.1, ts - 0.1))
        elif char == 'm':
            self.show_menu = not self.show_menu

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
            if self.show_menu:
                self.render_menu()
            else:
                display_type = self.config_manager.get('terminal.display_type', 'bar')
                if display_type == 'braille':
                    self.terminal_visualizer.render_braille(bars)
                elif display_type == 'line':
                    self.terminal_visualizer.render_line(bars)
                elif display_type == 'bi-directional':
                    self.terminal_visualizer.render_bidirectional(bars)
                else:
                    self.terminal_visualizer.render_bars(bars)

    def render_menu(self):
        self.terminal_visualizer.clear()
        print("=== Settings Menu ===")
        print(f"Volume:    {self.config_manager.get('processing.volume', 1.0):.1f} (+/-)")
        print(f"Pitch:     {self.config_manager.get('processing.pitch', 1.0):.1f} ([/])")
        print(f"Timescale: {self.config_manager.get('processing.timescale', 1.0):.1f} (k/l)")
        print(f"Display:   {self.config_manager.get('terminal.display_type', 'bar')} (t)")
        print(f"Input:     {self.config_manager.get('audio.input_type')} ")
        print("\nPress 'm' to close menu, 'q' to quit.")

    def start(self):
        print("Starting AudioVisualizer...")
        self.running = True
        self.server.start()
        self.keyboard.start()
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

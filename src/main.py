import sys
import os
import signal
import time
import threading
import queue
import numpy as np
from config.manager import ConfigManager
from audio.input import MicrophoneInput, FileInput
from audio.output import AudioOutput
from audio.processor import AudioProcessor
from audio.recorder import AudioRecorder
from visualizer.terminal import TerminalVisualizer
from visualizer.server import VisualizerServer
from utils.keyboard import KeyboardHandler

class AudioVisualizerApp:
    def __init__(self, config_path="config/default.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        self.config_manager.register_callback(self.on_config_change)
        
        self.processor = AudioProcessor(self.config_manager)
        self.output = AudioOutput(self.config_manager)
        self.recorder = AudioRecorder(self.config_manager)
        self.terminal_visualizer = TerminalVisualizer(self.config_manager)
        self.server = VisualizerServer(self.config_manager)
        self.server.on_toggle_recording = self.recorder.toggle
        self.server.is_recording_callback = lambda: self.recorder.recording
        self.keyboard = KeyboardHandler(self.handle_key)
        
        self.viz_queue = queue.Queue(maxsize=2)
        self.playback_queue = queue.Queue(maxsize=5)
        self.viz_thread = None
        self.playback_thread = None
        
        self.input = None
        self.init_input()
        self.running = False
        self.show_menu = False

    def init_input(self):
        if self.input:
            self.input.stop()
            
        input_type = self.config_manager.get('audio.input_type', 'microphone')
        if input_type == 'file':
            self.input = FileInput(self.config_manager)
        else:
            self.input = MicrophoneInput(self.config_manager)
            
        self.input.register_callback(self.audio_callback)
        if hasattr(self, 'running') and self.running:
            self.input.start()

    def on_config_change(self, key, value):
        if key in ['audio.input_type', 'audio.file_path']:
            self.init_input()
        if key == 'processing.volume':
            # Clear playback queue on volume change to make it feel responsive
            while not self.playback_queue.empty():
                try: self.playback_queue.get_nowait()
                except queue.Empty: break

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
            self.config_manager.set('processing.pitch', max(0.1, pitch - 0.1))
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
        elif char == 'p':
            profiles = list(self.terminal_visualizer.color_profiles.keys())
            current = self.config_manager.get('terminal.color_profile', 'default')
            new_idx = (profiles.index(current) + 1) % len(profiles) if current in profiles else 0
            self.config_manager.set('terminal.color_profile', profiles[new_idx])
        elif char == 'm':
            self.show_menu = not self.show_menu
        elif char == 'n':
            freq = self.config_manager.get('processing.modulation_freq', 0.0)
            self.config_manager.set('processing.modulation_freq', min(1000.0, freq + 10.0))
        elif char == 'b':
            freq = self.config_manager.get('processing.modulation_freq', 0.0)
            self.config_manager.set('processing.modulation_freq', max(0.0, freq - 10.0))
        elif char == 'u':
            lpf = self.config_manager.get('processing.lpf_cutoff', 20000.0)
            self.config_manager.set('processing.lpf_cutoff', min(20000.0, lpf + 500.0))
        elif char == 'j':
            lpf = self.config_manager.get('processing.lpf_cutoff', 20000.0)
            self.config_manager.set('processing.lpf_cutoff', max(100.0, lpf - 500.0))
        elif char == 'y':
            hpf = self.config_manager.get('processing.hpf_cutoff', 0.0)
            self.config_manager.set('processing.hpf_cutoff', min(10000.0, hpf + 100.0))
        elif char == 'h':
            hpf = self.config_manager.get('processing.hpf_cutoff', 0.0)
            self.config_manager.set('processing.hpf_cutoff', max(0.0, hpf - 100.0))
        elif char == 'r':
            self.recorder.toggle()
        elif char == 'c':
            # Reset effects
            self.config_manager.set('processing.volume', 1.0)
            self.config_manager.set('processing.pitch', 1.0)
            self.config_manager.set('processing.timescale', 1.0)
            self.config_manager.set('processing.modulation_freq', 0.0)
            self.config_manager.set('processing.lpf_cutoff', 20000.0)
            self.config_manager.set('processing.hpf_cutoff', 0.0)

    def audio_callback(self, data):
        # Apply transformations (volume, pitch, etc.)
        processed_data = self.processor.apply_transformations(data)
        
        # Write to recorder
        self.recorder.write(processed_data)
        
        # Push to playback queue
        try:
            self.playback_queue.put(processed_data, timeout=0.1)
        except queue.Full:
            pass
        
        # Push to visualization queue (non-blocking)
        try:
            self.viz_queue.put_nowait(processed_data)
        except queue.Full:
            pass

    def playback_loop(self):
        while self.running:
            try:
                data = self.playback_queue.get(timeout=0.1)
                self.output.play(data)
                self.playback_queue.task_done()
            except queue.Empty:
                continue

    def visualization_loop(self):
        while self.running:
            try:
                processed_data = self.viz_queue.get(timeout=0.1)
            except queue.Empty:
                continue

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
                    # If multi-channel, average for terminal
                    terminal_bars = bars
                    if isinstance(bars, list):
                        terminal_bars = np.mean(bars, axis=0)
                    
                    display_type = self.config_manager.get('terminal.display_type', 'bar')
                    if display_type == 'braille':
                        self.terminal_visualizer.render_braille(terminal_bars)
                    elif display_type == 'line':
                        self.terminal_visualizer.render_line(terminal_bars)
                    elif display_type == 'bi-directional':
                        self.terminal_visualizer.render_bidirectional(terminal_bars)
                    else:
                        self.terminal_visualizer.render_bars(terminal_bars)

    def render_menu(self):
        self.terminal_visualizer.clear()
        print("=== Settings Menu ===")
        print(f"Volume:     {self.config_manager.get('processing.volume', 1.0):.1f} (+/-)")
        print(f"Pitch:      {self.config_manager.get('processing.pitch', 1.0):.1f} ([/])")
        print(f"Timescale:  {self.config_manager.get('processing.timescale', 1.0):.1f} (k/l)")
        print(f"Mod Freq:   {self.config_manager.get('processing.modulation_freq', 0.0):.1f} (b/n)")
        print(f"LPF Cutoff: {self.config_manager.get('processing.lpf_cutoff', 20000.0):.0f} (j/u)")
        print(f"HPF Cutoff: {self.config_manager.get('processing.hpf_cutoff', 0.0):.0f} (h/y)")
        print(f"Display:    {self.config_manager.get('terminal.display_type', 'bar')} (t)")
        print(f"Color:      {self.config_manager.get('terminal.color_profile', 'default')} (p)")
        print(f"Recording:  {'ON' if self.recorder.recording else 'OFF'} (r)")
        print(f"Input:      {self.config_manager.get('audio.input_type')} ")
        print(f"File:       {os.path.basename(self.config_manager.get('audio.file_path', 'N/A'))}")
        print("\nPress 'c' to reset all effects.")
        print("Press 'm' to close menu, 'q' to quit.")

    def start(self):
        print("Starting AudioVisualizer...")
        self.running = True
        self.server.start()
        self.keyboard.start()
        
        # Start threads
        self.viz_thread = threading.Thread(target=self.visualization_loop, daemon=True)
        self.viz_thread.start()
        
        self.playback_thread = threading.Thread(target=self.playback_loop, daemon=True)
        self.playback_thread.start()
        
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
        if self.viz_thread:
            self.viz_thread.join(timeout=1.0)
        if self.playback_thread:
            self.playback_thread.join(timeout=1.0)

if __name__ == "__main__":
    app = AudioVisualizerApp()
    app.start()

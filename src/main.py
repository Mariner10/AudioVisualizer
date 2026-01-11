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
from utils.state import StateMachine, AppState, PlaybackState, RecordingState

from utils.logger import logger

class AudioVisualizerApp:
    def __init__(self, config_path="config/default.yaml"):
        logger.info(f"Initializing AudioVisualizerApp with config: {config_path}")
        self.state_machine = StateMachine()
        self.state_machine.set_app_state(AppState.STARTING)
        
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        self.config_manager.register_callback(self.on_config_change)
        
        self.processor = AudioProcessor(self.config_manager)
        self.output = AudioOutput(self.config_manager)
        self.recorder = AudioRecorder(self.config_manager, self.state_machine)
        self.terminal_visualizer = TerminalVisualizer(self.config_manager)
        self.server = VisualizerServer(self.config_manager)
        self.server.on_toggle_recording = self.recorder.toggle
        self.server.is_recording_callback = lambda: self.recorder.recording
        self.keyboard = KeyboardHandler(self.handle_key)
        
        self.viz_queue = queue.Queue(maxsize=2)
        self.playback_queue = queue.Queue(maxsize=5)
        self.viz_thread = None
        self.playback_thread = None
        self.tui = None
        
        self.input = None
        self.init_input()
        self.running = False
        self.show_menu = False

    def init_input(self):
        if self.input:
            logger.info("Stopping existing input stream")
            self.input.stop()
            
        input_type = self.config_manager.get('audio.input_type', 'microphone')
        logger.info(f"Initializing input type: {input_type}")
        if input_type == 'file':
            self.input = FileInput(self.config_manager)
        else:
            self.input = MicrophoneInput(self.config_manager)
            
        self.input.register_callback(self.audio_callback)
        if hasattr(self, 'running') and self.running:
            self.input.start()

    def on_config_change(self, key, value):
        logger.debug(f"Config changed: {key} = {value}")
        if key in ['audio.input_type', 'audio.file_path']:
            self.init_input()
        if key == 'processing.volume':
            # Clear playback queue on volume change to make it feel responsive
            while not self.playback_queue.empty():
                try: self.playback_queue.get_nowait()
                except queue.Empty: break

    def handle_key(self, char):
        logger.debug(f"Key pressed: {char}")
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
            logger.info("Resetting all audio effects")
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
        logger.info("Starting playback loop")
        self.state_machine.set_playback_state(PlaybackState.PLAYING)
        while self.running:
            try:
                data = self.playback_queue.get(timeout=0.1)
                self.output.play(data)
                self.playback_queue.task_done()
            except queue.Empty:
                continue
        self.state_machine.set_playback_state(PlaybackState.STOPPED)

    def visualization_loop(self):
        logger.info("Starting visualization loop")
        while self.running:
            try:
                processed_data = self.viz_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # Process FFT
            magnitudes, frequencies = self.processor.process_fft(processed_data)
            
            # Simple beat detection (use the first channel if stereo)
            m_beat = magnitudes[0] if isinstance(magnitudes, list) else magnitudes
            is_beat = self.processor.detect_beat(m_beat, frequencies)

            # Get bars for visualization
            num_bars = self.config_manager.get('visualizer.num_bars', 64)
            bars = self.processor.get_bars(magnitudes, frequencies, num_bars=num_bars)
            
            # Send to browser
            self.server.send_data(bars, is_beat=is_beat)
            
            # Render in terminal if enabled
            if self.config_manager.get('visualizer.type') == 'terminal':
                # If multi-channel, average for terminal
                terminal_bars = bars
                if isinstance(bars, list):
                    terminal_bars = np.mean(bars, axis=0)
                
                if self.tui:
                    self.tui.call_from_thread(self.tui.set_bars, terminal_bars, is_beat=is_beat)
                elif self.show_menu:
                    self.render_menu()
                else:
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
        sys.stdout.write("=== Settings Menu ===\n")
        sys.stdout.write(f"Volume:     {self.config_manager.get('processing.volume', 1.0):.1f} (+/-)\n")
        sys.stdout.write(f"Pitch:      {self.config_manager.get('processing.pitch', 1.0):.1f} ([/])\n")
        sys.stdout.write(f"Timescale:  {self.config_manager.get('processing.timescale', 1.0):.1f} (k/l)\n")
        sys.stdout.write(f"Mod Freq:   {self.config_manager.get('processing.modulation_freq', 0.0):.1f} (b/n)\n")
        sys.stdout.write(f"LPF Cutoff: {self.config_manager.get('processing.lpf_cutoff', 20000.0):.0f} (j/u)\n")
        sys.stdout.write(f"HPF Cutoff: {self.config_manager.get('processing.hpf_cutoff', 0.0):.0f} (h/y)\n")
        sys.stdout.write(f"Display:    {self.config_manager.get('terminal.display_type', 'bar')} (t)\n")
        sys.stdout.write(f"Color:      {self.config_manager.get('terminal.color_profile', 'default')} (p)\n")
        sys.stdout.write(f"Recording:  {'ON' if self.recorder.recording else 'OFF'} (r)\n")
        sys.stdout.write(f"Input:      {self.config_manager.get('audio.input_type')} \n")
        sys.stdout.write(f"File:       {os.path.basename(self.config_manager.get('audio.file_path', 'N/A'))}\n")
        sys.stdout.write("\nPress 'c' to reset all effects.\n")
        sys.stdout.write("Press 'm' to close menu, 'q' to quit.\n")
        sys.stdout.flush()

    def start(self):
        logger.info("Starting AudioVisualizer application")
        self.running = True
        self.state_machine.set_app_state(AppState.RUNNING)
        self.server.start()
        
        # Start threads
        self.viz_thread = threading.Thread(target=self.visualization_loop, daemon=True)
        self.viz_thread.start()
        
        self.playback_thread = threading.Thread(target=self.playback_loop, daemon=True)
        self.playback_thread.start()
        
        self.input.start()

        if self.config_manager.get('visualizer.type') == 'terminal':
            try:
                from visualizer.tui import AudioVisualizerTUI
                self.tui = AudioVisualizerTUI(self)
                self.tui.run()
            except Exception as e:
                logger.error(f"Failed to start TUI: {e}")
                # Fallback to keyboard handler
                self.keyboard.start()
                while self.running:
                    time.sleep(0.1)
            finally:
                self.stop()
        else:
            self.keyboard.start()
            try:
                while self.running:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        if not self.running:
            return
            
        logger.info("Stopping AudioVisualizer application")
        self.running = False
        self.state_machine.set_app_state(AppState.STOPPING)
        
        if self.input:
            self.input.stop()
        if self.output:
            self.output.stop()
        if self.recorder:
            self.recorder.stop()
        if self.server:
            self.server.stop()
        if self.keyboard:
            self.keyboard.stop()
            
        self.state_machine.set_app_state(AppState.IDLE)





if __name__ == "__main__":
    app = AudioVisualizerApp()
    app.start()

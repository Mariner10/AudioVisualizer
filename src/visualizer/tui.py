import numpy as np
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Label, Slider, Switch, Button
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.binding import Binding
from textual.reactive import reactive
from textual import work
from rich.text import Text
from rich.console import Console, ConsoleOptions, RenderResult
from rich.measure import Measurement
import asyncio

class VisualizerWidget(Static):
    """Custom widget for audio visualization using Braille characters."""
    bars = reactive([])
    display_type = reactive("bar")
    color_profile = reactive("default")

    def render(self) -> RenderResult:
        if not self.bars or len(self.bars) == 0:
            return Text("Waiting for audio data...", style="dim")
        
        width = self.size.width
        height = self.size.height
        
        if width <= 0 or height <= 0:
            return Text("")

        # Get bars and scale them
        bars = np.array(self.bars)
        num_bars = len(bars)
        
        # Scale to width
        if num_bars > width:
            # Simple downsampling
            indices = np.linspace(0, num_bars - 1, width).astype(int)
            bars = bars[indices]
        
        max_val = np.max(bars) if np.max(bars) > 0 else 1
        
        if self.display_type == "braille":
            return self._render_braille(bars, width, height, max_val)
        else:
            return self._render_bars(bars, width, height, max_val)

    def _render_bars(self, bars, width, height, max_val) -> Text:
        scaled_bars = (bars / max_val * height).astype(int)
        
        lines = []
        for h in range(height - 1, -1, -1):
            chars = []
            for val in scaled_bars:
                if val > h:
                    chars.append("┃")
                else:
                    chars.append(" ")
            lines.append("".join(chars))
        
        return Text("\n".join(lines), style="green")

    def _render_braille(self, bars, width, height, max_val) -> Text:
        # Braille dots: 2 wide, 4 high
        dot_width = width * 2
        dot_height = height * 4
        
        if len(bars) != dot_width:
            indices = np.linspace(0, len(bars) - 1, dot_width).astype(int)
            bars = bars[indices]
            
        scaled_bars = (bars / max_val * dot_height).astype(int)
        
        lines = []
        for row in range(height - 1, -1, -1):
            line_chars = []
            for col in range(0, dot_width, 2):
                left_val = scaled_bars[col]
                right_val = scaled_bars[col+1] if col+1 < dot_width else 0
                
                code = 0
                # Left column dots (1, 2, 3, 7)
                l_fill = max(0, min(4, left_val - row * 4))
                if l_fill > 0: code |= (1 << 0)
                if l_fill > 1: code |= (1 << 1)
                if l_fill > 2: code |= (1 << 2)
                if l_fill > 3: code |= (1 << 6)
                
                # Right column dots (4, 5, 6, 8)
                r_fill = max(0, min(4, right_val - row * 4))
                if r_fill > 0: code |= (1 << 3)
                if r_fill > 1: code |= (1 << 4)
                if r_fill > 2: code |= (1 << 5)
                if r_fill > 3: code |= (1 << 7)
                
                char = chr(0x2800 + code) if code > 0 else " "
                line_chars.append(char)
            lines.append("".join(line_chars))
            
        return Text("\n".join(lines), style="cyan")

class SettingsSidebar(Vertical):
    """Sidebar for settings."""
    def compose(self) -> ComposeResult:
        yield Label("Settings", id="sidebar-title")
        
        with Vertical(classes="setting-group"):
            yield Label("Volume")
            yield Slider(min=0, max=200, value=100, id="volume-slider")
            
        with Vertical(classes="setting-group"):
            yield Label("Pitch")
            yield Slider(min=10, max=200, value=100, id="pitch-slider")

        with Vertical(classes="setting-group"):
            yield Label("Timescale")
            yield Slider(min=10, max=200, value=100, id="timescale-slider")
            
        with Horizontal(classes="setting-group"):
            yield Label("Recording")
            yield Switch(id="recording-switch")
            
        yield Button("Reset Effects", variant="error", id="reset-button")
        yield Label("\n[Controls]\nQ: Quit\nM: Toggle Settings\n+/-: Volume\n[/]: Pitch\nR: Record\nT: Display Type", classes="help-text")

class AudioVisualizerTUI(App):
    CSS = """
    #main-container {
        layout: horizontal;
    }
    
    VisualizerWidget {
        width: 1fr;
        height: 100%;
        border: solid green;
        padding: 0 1;
    }
    
    SettingsSidebar {
        width: 35;
        height: 100%;
        border: solid blue;
        padding: 1;
        background: $surface;
    }
    
    .setting-group {
        margin-bottom: 1;
        height: auto;
    }
    
    #sidebar-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        background: $primary;
        color: white;
    }
    
    .help-text {
        font-size: 80%;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("m", "toggle_sidebar", "Settings"),
        Binding("plus", "increment_volume", "Vol+"),
        Binding("minus", "decrement_volume", "Vol-"),
        Binding("r", "toggle_recording", "Record"),
        Binding("t", "cycle_display_type", "Display"),
        Binding("right_bracket", "increment_pitch", "Pitch+"),
        Binding("left_bracket", "decrement_pitch", "Pitch-"),
    ]

    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.config_manager = app_instance.config_manager

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            yield VisualizerWidget(id="visualizer")
            yield SettingsSidebar(id="sidebar")
        yield Footer()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(SettingsSidebar)
        sidebar.visible = not sidebar.visible

    def action_increment_volume(self) -> None:
        self.app_instance.handle_key('+')
        self._sync_sliders()

    def action_decrement_volume(self) -> None:
        self.app_instance.handle_key('-')
        self._sync_sliders()

    def action_increment_pitch(self) -> None:
        self.app_instance.handle_key(']')
        self._sync_sliders()

    def action_decrement_pitch(self) -> None:
        self.app_instance.handle_key('[')
        self._sync_sliders()

    def action_cycle_display_type(self) -> None:
        self.app_instance.handle_key('t')
        viz = self.query_one(VisualizerWidget)
        viz.display_type = self.config_manager.get('terminal.display_type', 'bar')

    def action_toggle_recording(self) -> None:
        self.app_instance.handle_key('r')
        self.query_one("#recording-switch").value = self.app_instance.recorder.recording

    def _sync_sliders(self) -> None:
        """Sync TUI sliders with config values."""
        self.query_one("#volume-slider").value = int(self.config_manager.get('processing.volume', 1.0) * 100)
        self.query_one("#pitch-slider").value = int(self.config_manager.get('processing.pitch', 1.0) * 100)
        self.query_one("#timescale-slider").value = int(self.config_manager.get('processing.timescale', 1.0) * 100)

    def on_mount(self) -> None:
        self.query_one(VisualizerWidget).display_type = self.config_manager.get('terminal.display_type', 'bar')
        self._sync_sliders()
        self.update_visualizer()

    @work(exclusive=True)
    async def update_visualizer(self) -> None:
        while True:
            # We use the viz_queue from the app instance
            if not self.app_instance.viz_queue.empty():
                try:
                    # In a real app we might want to consume from the queue here
                    # But the main loop also consumes from it.
                    # Let's see how we can share it.
                    # For now, let's assume this is the ONLY consumer for terminal viz.
                    pass
                except Exception:
                    pass
            
            # Since the main loop is also running, maybe we should have the main loop
            # push to the TUI instead.
            await asyncio.sleep(0.05)

    def set_bars(self, bars):
        self.query_one(VisualizerWidget).bars = bars

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "reset-button":
            self.app_instance.handle_key('c')
            self._sync_sliders()

    def on_slider_changed(self, event: Slider.Changed) -> None:
        if event.slider.id == "volume-slider":
            self.config_manager.set('processing.volume', event.value / 100.0)
        elif event.slider.id == "pitch-slider":
            self.config_manager.set('processing.pitch', event.value / 100.0)
        elif event.slider.id == "timescale-slider":
            self.config_manager.set('processing.timescale', event.value / 100.0)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id == "recording-switch":
            if event.value != self.app_instance.recorder.recording:
                self.app_instance.recorder.toggle()


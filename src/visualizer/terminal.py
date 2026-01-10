import os
import sys
import shutil
import numpy as np
import yaml
from .utils import get_color_gradient

class TerminalVisualizer:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.display_type = config_manager.get('terminal.display_type', 'bar')
        self.width, self.height = shutil.get_terminal_size()
        self.color_profiles = self.load_color_profiles()

    def load_color_profiles(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'colors.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f).get('profiles', {})
        return {}

    def get_current_colors(self, bars):
        profile_name = self.config_manager.get('terminal.color_profile', 'default')
        profile = self.color_profiles.get(profile_name, self.color_profiles.get('default', {}))
        
        profile_type = profile.get('type', 'frequency')
        colors = profile.get('colors', ['#ffffff'])
        
        if profile_type == 'solid':
            color = profile.get('color', colors[0])
            ansi = get_color_gradient([color], 1)[0]
            return [ansi] * len(bars)
            
        if profile_type == 'amplitude':
            # Map bar value to color gradient
            max_val = np.max(bars) if np.max(bars) > 0 else 1
            # We want to pick a color from the gradient based on the bar's relative amplitude
            gradient = get_color_gradient(colors, 100)
            result = []
            for val in bars:
                idx = int(min(val / max_val * 99, 99))
                result.append(gradient[idx])
            return result
            
        # Default: frequency / gradient
        return get_color_gradient(colors, len(bars))

    def update_size(self):
        self.width, self.height = shutil.get_terminal_size()

    def clear(self):
        sys.stdout.write("\033[H")
        sys.stdout.flush()

    def render_bars(self, bars):
        """
        Render audio bars using ASCII.
        """
        self.update_size()
        num_bars = min(len(bars), self.width)
        bars_subset = bars[:num_bars]
        max_val = np.max(bars_subset) if np.max(bars_subset) > 0 else 1
        
        display_type = self.config_manager.get('terminal.display_type', 'bar')
        if display_type == 'bi-directional':
            return self.render_bidirectional(bars)

        scaled_bars = (bars_subset / max_val * (self.height - 2)).astype(int)
        colors = self.get_current_colors(bars_subset)

        output = []
        # Pre-build color components to avoid repeat lookups
        ansi_colors = [f"{c}┃\033[0m" for c in colors]
        
        for h in range(self.height - 2, -1, -1):
            line_chars = [ansi_colors[i] if val > h else " " for i, val in enumerate(scaled_bars)]
            output.append("".join(line_chars))
        
        self.clear()
        sys.stdout.write("\n".join(output) + "\n")
        sys.stdout.flush()

    def render_bidirectional(self, bars):
        self.update_size()
        num_bars = min(len(bars), self.width)
        bars_subset = bars[:num_bars]
        max_val = np.max(bars_subset) if np.max(bars_subset) > 0 else 1
        
        half_height = (self.height - 2) // 2
        scaled_bars = (bars_subset / max_val * half_height).astype(int)
        colors = self.get_current_colors(bars_subset)
        ansi_colors = [f"{c}┃\033[0m" for c in colors]
        center_colors = [f"{c}━\033[0m" for c in colors]

        output = []
        for h in range(half_height, -half_height - 1, -1):
            if h > 0:
                line_chars = [ansi_colors[i] if val >= h else " " for i, val in enumerate(scaled_bars)]
            elif h < 0:
                abs_h = abs(h)
                line_chars = [ansi_colors[i] if val >= abs_h else " " for i, val in enumerate(scaled_bars)]
            else: # center line
                line_chars = center_colors
            output.append("".join(line_chars))
            
        self.clear()
        sys.stdout.write("\n".join(output) + "\n")
        sys.stdout.flush()

    def render_line(self, bars):
        """
        Render a smooth line using Braille.
        """
        self.update_size()
        num_points = min(len(bars), self.width * 2)
        bars_subset = bars[:num_points]
        max_val = np.max(bars_subset) if np.max(bars_subset) > 0 else 1
        dot_height = self.height * 4
        scaled_points = (bars_subset / max_val * (dot_height - 1)).astype(int)
        
        if len(scaled_points) % 2 != 0:
            scaled_points = np.append(scaled_points, 0)
            
        colors = self.get_current_colors(bars_subset[::2]) # One color per braille char
            
        output = []
        for row in range(self.height - 1, -1, -1):
            line = ""
            for i, col in enumerate(range(0, len(scaled_points), 2)):
                lp = scaled_points[col]
                rp = scaled_points[col+1]
                
                code = 0
                l_dot_pos = lp - row * 4
                if 0 <= l_dot_pos < 4:
                    dot_idx = [0, 1, 2, 6][int(l_dot_pos)]
                    code |= (1 << dot_idx)
                
                r_dot_pos = rp - row * 4
                if 0 <= r_dot_pos < 4:
                    dot_idx = [3, 4, 5, 7][int(r_dot_pos)]
                    code |= (1 << dot_idx)
                
                char = chr(0x2800 + code) if code > 0 else " "
                color = colors[i] if i < len(colors) else "\033[0m"
                line += f"{color}{char}\033[0m"
            output.append(line)
            
        self.clear()
        sys.stdout.write("\n".join(output) + "\n")
        sys.stdout.flush()

    def render_braille(self, bars):
        """
        Render audio bars using Braille dots for higher resolution.
        """
        self.update_size()
        num_bars = min(len(bars), self.width * 2)
        bars_subset = bars[:num_bars]
        max_val = np.max(bars_subset) if np.max(bars_subset) > 0 else 1
        dot_height = self.height * 4
        scaled_bars = (bars_subset / max_val * dot_height).astype(int)
        
        if len(scaled_bars) % 2 != 0:
            scaled_bars = np.append(scaled_bars, 0)
            
        colors = self.get_current_colors(bars_subset[::2]) # One color per braille char
            
        output = []
        for row in range(self.height - 1, -1, -1):
            line = ""
            for i, col in enumerate(range(0, len(scaled_bars), 2)):
                left_val = scaled_bars[col]
                right_val = scaled_bars[col+1]
                
                l_dots = [0, 0, 0, 0]
                l_fill = max(0, min(4, left_val - row * 4))
                for j in range(l_fill): l_dots[j] = 1
                
                r_dots = [0, 0, 0, 0]
                r_fill = max(0, min(4, right_val - row * 4))
                for j in range(r_fill): r_dots[j] = 1
                
                code = 0
                if l_dots[0]: code |= (1 << 0)
                if l_dots[1]: code |= (1 << 1)
                if l_dots[2]: code |= (1 << 2)
                if r_dots[0]: code |= (1 << 3)
                if r_dots[1]: code |= (1 << 4)
                if r_dots[2]: code |= (1 << 5)
                if l_dots[3]: code |= (1 << 6)
                if r_dots[3]: code |= (1 << 7)
                
                color = colors[i] if i < len(colors) else "\033[0m"
                line += f"{color}{chr(0x2800 + code)}\033[0m"
            output.append(line)
            
        self.clear()
        sys.stdout.write("\n".join(output) + "\n")
        sys.stdout.flush()

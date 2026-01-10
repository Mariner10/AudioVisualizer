import os
import sys
import shutil
import numpy as np

class TerminalVisualizer:
    def __init__(self, config):
        self.config = config
        self.display_type = config.get('terminal.display_type', 'bar')
        self.width, self.height = shutil.get_terminal_size()

    def update_size(self):
        self.width, self.height = shutil.get_terminal_size()

    def clear(self):
        # Move cursor to top-left instead of clearing the whole screen for smoother updates
        sys.stdout.write("\033[H")
        sys.stdout.flush()

    def render_bars(self, bars):
        """
        Render audio bars using ASCII.
        bars: array of magnitudes
        """
        self.update_size()
        num_bars = min(len(bars), self.width)
        
        # Scale bars to terminal height
        max_val = np.max(bars) if np.max(bars) > 0 else 1
        scaled_bars = (bars[:num_bars] / max_val * (self.height - 2)).astype(int)

        output = []
        for h in range(self.height - 2, -1, -1):
            line = ""
            for val in scaled_bars:
                if val > h:
                    line += "┃"
                else:
                    line += " "
            output.append(line)
        
        self.clear()
        sys.stdout.write("\n".join(output) + "\n")
        sys.stdout.flush()

    def render_braille(self, bars):
        """
        Render audio bars using Braille dots for higher resolution.
        Each Braille character is 2 dots wide and 4 dots high.
        """
        self.update_size()
        
        # We use 2 columns of dots per Braille character
        # So we can show 2 * width bars
        num_bars = min(len(bars), self.width * 2)
        max_val = np.max(bars) if np.max(bars) > 0 else 1
        
        # Scale to dot height (height * 4)
        dot_height = self.height * 4
        scaled_bars = (bars[:num_bars] / max_val * dot_height).astype(int)
        
        # Pad bars if needed to make it even
        if len(scaled_bars) % 2 != 0:
            scaled_bars = np.append(scaled_bars, 0)
            
        output = []
        for row in range(self.height - 1, -1, -1):
            line = ""
            for col in range(0, len(scaled_bars), 2):
                left_val = scaled_bars[col]
                right_val = scaled_bars[col+1]
                
                # Calculate dots for this Braille character (2x4)
                # Left dots (1, 2, 3, 7)
                l_dots = [0, 0, 0, 0]
                l_fill = max(0, min(4, left_val - row * 4))
                for i in range(l_fill):
                    l_dots[i] = 1
                
                # Right dots (4, 5, 6, 8)
                r_dots = [0, 0, 0, 0]
                r_fill = max(0, min(4, right_val - row * 4))
                for i in range(r_fill):
                    r_dots[i] = 1
                
                # Map to Braille unicode
                # 1 4
                # 2 5
                # 3 6
                # 7 8
                code = 0
                if l_dots[0]: code |= (1 << 0)
                if l_dots[1]: code |= (1 << 1)
                if l_dots[2]: code |= (1 << 2)
                if r_dots[0]: code |= (1 << 3)
                if r_dots[1]: code |= (1 << 4)
                if r_dots[2]: code |= (1 << 5)
                if l_dots[3]: code |= (1 << 6)
                if r_dots[3]: code |= (1 << 7)
                
                line += chr(0x2800 + code)
            output.append(line)
            
        self.clear()
        sys.stdout.write("\n".join(output) + "\n")
        sys.stdout.flush()

import os
import sys
import shutil

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
        Render audio bars using Braille or ASCII.
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
        print("\n".join(output))

    def render_braille(self, bars):
        """
        Render audio bars using Braille dots for higher resolution.
        """
        self.update_size()
        # Each Braille char is 2 dots wide and 4 dots high
        # For simplicity, let's start with a simpler 1-dot wide version
        num_bars = min(len(bars), self.width)
        max_val = np.max(bars) if np.max(bars) > 0 else 1
        
        # Braille dots mapping (simplified for vertical bars)
        braille_chars = [" ", "⠂", "⠒", "⠖", "⠶", "⠷", "⠿"] # Simplified vertical dots
        # Actually, let's use the standard Braille block for vertical bars
        # ⠁ ⠃ ⠇ ⡇
        vertical_braille = [" ", "⠁", "⠃", "⠇", "⡇"]
        
        scaled_bars = (bars[:num_bars] / max_val * (self.height * 4)).astype(int)
        
        output = []
        for h_block in range(self.height - 1, -1, -1):
            line = ""
            for val in scaled_bars:
                dots_in_block = max(0, min(4, val - h_block * 4))
                line += vertical_braille[dots_in_block]
            output.append(line)
        
        self.clear()
        sys.stdout.write("\n".join(output) + "\n")
        sys.stdout.flush()

import numpy as np # Needed for render methods

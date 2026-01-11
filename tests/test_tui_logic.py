import unittest
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from visualizer.tui import VisualizerWidget

class TestTUILogic(unittest.TestCase):
    def test_braille_rendering_logic(self):
        # We can't easily test the Textual Widget's render() without a terminal
        # but we can test the internal _render_braille if we make it accessible
        # or just test that the math for Braille dots is correct.
        
        widget = VisualizerWidget()
        
        # Test with 2 bars, width 1, height 1
        # Braille char for 2 dots high on both sides
        # Left dots: 1, 2. Right dots: 4, 5.
        # (1<<0) | (1<<1) | (1<<3) | (1<<4) = 1 | 2 | 8 | 16 = 27
        # Braille: 0x2800 + 27 = 0x281B
        
        bars = np.array([4, 4]) # Max height for 1 row (4 dots)
        max_val = 4
        width = 1
        height = 1
        profile = {"type": "solid", "colors": ["#ffffff"]}
        
        result = widget._render_braille(bars, width, height, max_val, profile)
        char = str(result).strip()
        self.assertEqual(len(char), 1)
        self.assertEqual(ord(char), 0x2800 + 0xFF) # Full braille block since both are 4/4
        
    def test_empty_bars(self):
        widget = VisualizerWidget()
        result = widget.render()
        self.assertIn("Waiting", str(result))

if __name__ == '__main__':
    unittest.main()

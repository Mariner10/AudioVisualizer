def hex_to_ansi(hex_color):
    """
    Convert hex color to ANSI escape code (24-bit color).
    """
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"\033[38;2;{r};{g};{b}m"
    return "\033[0m"

def get_color_gradient(colors, steps):
    """
    Generate a gradient of colors.
    """
    import numpy as np
    
    if not colors:
        return ["\033[0m"] * steps
        
    def hex_to_rgb(h):
        h = h.lstrip('#')
        return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)])

    rgbs = [hex_to_rgb(c) for c in colors]
    if len(rgbs) == 1:
        r, g, b = rgbs[0]
        return [f"\033[38;2;{r};{g};{b}m"] * steps

    result = []
    for i in range(steps):
        # Determine which two colors to interpolate between
        pos = i / (steps - 1) if steps > 1 else 0
        idx = min(int(pos * (len(rgbs) - 1)), len(rgbs) - 2)
        local_pos = (pos * (len(rgbs) - 1)) - idx
        
        rgb = rgbs[idx] * (1 - local_pos) + rgbs[idx+1] * local_pos
        r, g, b = rgb.astype(int)
        result.append(f"\033[38;2;{r};{g};{b}m")
    
    return result

def get_hex_gradient(colors, steps):
    """
    Generate a gradient of hex colors.
    """
    import numpy as np
    
    if not colors:
        return ["#ffffff"] * steps
        
    def hex_to_rgb(h):
        h = h.lstrip('#')
        return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)])

    rgbs = [hex_to_rgb(c) for c in colors]
    if len(rgbs) == 1:
        return [colors[0]] * steps

    result = []
    for i in range(steps):
        pos = i / (steps - 1) if steps > 1 else 0
        idx = min(int(pos * (len(rgbs) - 1)), len(rgbs) - 2)
        local_pos = (pos * (len(rgbs) - 1)) - idx
        
        rgb = rgbs[idx] * (1 - local_pos) + rgbs[idx+1] * local_pos
        r, g, b = rgb.astype(int)
        result.append(f"#{r:02x}{g:02x}{b:02x}")
    
    return result

# AudioVisualizer

A vastly customizable audio tool with visualizer that can utilize the live microphone as well as input MP3, WAV, FLAC files.

## Features

- **Multi-Frontend Support**: 
  - **Terminal**: High-resolution visualization using Braille dots, ASCII bars, and more. Includes a live settings menu and keybindings.
  - **Browser**: Smooth, colorful rendering using HTML5 Canvas and WebSockets for real-time data.
- **Advanced Audio Processing**:
  - **High Performance**: Optimized using Numpy/Scipy with decoupled visualization threads for minimal audio latency.
  - Live editing of **Volume**, **Pitch**, and **Timescale**.
  - **Modulation**: Ring Modulation and Amplitude Modulation (AM) with persistent phase to prevent audio clicks.
  - **Stereo Support**: Independent FFT processing and correct multi-channel transformation handling.
- **Customizable Color Profiles**:
  - Define profiles in `config/colors.yaml`.
  - Support for **Frequency-based**, **Amplitude-based**, and **Solid** color modes.
- **Dynamic Configuration**:
  - All settings are stored in `config/default.yaml`.
  - Real-time updates from both Terminal and Browser frontends.
  - Browser-based **File Selector** for easy audio file switching.

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. (Optional) Install `pyaudio` dependencies if not already present (e.g., `portaudio`).

## Usage

Start the application:
```bash
python src/main.py
```

### Keybindings (Terminal)
- `q`: Quit
- `m`: Toggle Settings Menu
- `+`/`-`: Adjust Volume
- `[`/`]`: Adjust Pitch
- `k`/`l`: Adjust Timescale
- `b`/`n`: Adjust Modulation Frequency
- `t`: Cycle Display Types
- `p`: Cycle Color Profiles

## Development

- **Source Code**: Located in `src/`.
- **Tests**: Run using `python -m unittest discover tests`.
- **Config**: Edit `config/default.yaml` and `config/colors.yaml`.

## License

MIT

# TODO: AudioVisualizer

## Phase 1: Foundation & CLI Visualizer
- [ ] Initialize Python project structure (pyproject.toml or requirements.txt)
- [ ] Implement configuration system (YAML/JSON)
- [ ] Implement Audio Input Module (File and Microphone using PyAudio)
- [ ] Implement FFT Processing Module (NumPy)
- [ ] Implement Basic Terminal Visualizer (Braille dots/ASCII)
- [ ] Implement Audio Output (Playback while visualizing)

## Phase 2: Live Editing & Refinement
- [ ] Implement Live Audio Editing (Volume, Pitch, Timescale)
- [ ] Add support for modular display types in Terminal
- [ ] Add support for color profiles in Terminal

## Phase 3: Web Frontend
- [ ] Setup Web Server (FastAPI/Flask)
- [ ] Implement WebSocket for real-time visualization data
- [ ] Build Browser-based visualizer (Canvas/WebGL)

## Phase 4: Testing & Optimization
- [ ] Write unit tests for FFT and processing
- [ ] Optimize with Multiprocessing
- [ ] Finalize configuration UI in both frontends
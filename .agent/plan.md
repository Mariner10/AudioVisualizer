# Improvement Plan - AudioVisualizer

## Phase 1: Foundation & TUI
- [ ] Initialize logging system (src/utils/logger.py).
- [ ] Refactor Terminal Visualizer to use `Textual` for a robust TUI.
    - [ ] Main visualization area.
    - [ ] Sidebar/Modal for settings.
    - [ ] Integrated keyboard handling.
- [ ] Improve configuration management (validation).

## Phase 2: Web Visualizer
- [ ] Integrate Tailwind CSS into `src/visualizer/static/index.html`.
- [ ] Refactor web UI for a more modern look and feel.
- [ ] Optimize WebSocket data transfer.

## Phase 3: Audio & Stability
- [ ] Add robust error handling for audio stream initialization.
- [ ] Implement a proper state machine for audio playback/recording.
- [ ] Optimize FFT processing if necessary.

## Phase 4: Quality Assurance
- [ ] Expand tests in `tests/`.
- [ ] Final documentation update.

# Task List - AudioVisualizer Phase 2 (Enhancements) (COMPLETED)

## 1. Color System Improvements
- [x] Implement color based on amplitude in `TerminalVisualizer`.
- [x] Respect color profile `type` (solid, frequency, amplitude) in `TerminalVisualizer`.
- [x] Sync color profiles to Browser frontend.
- [x] Implement color profiles in Browser frontend (Canvas rendering).

## 2. Audio Processing Enhancements
- [x] Implement a more robust "Modulation" system (Carrier frequency adjustment, etc.).
- [x] Improve Pitch Shifting (Resampling implemented).
- [x] Add "Stereo" support (Independent FFT per channel).

## 3. UI/UX Improvements
- [x] Add more info to the Terminal Settings Menu.
- [x] Improve Browser UI (better sliders, color profile selector).
- [x] Add a "File Selector" for the browser if in file mode.

## 4. Documentation & Maintenance
- [x] Update README.md with current features and instructions.
- [x] Add more comprehensive tests for audio transformations.

## 5. Efficiency & Performance
- [x] Optimized processing with Numpy/Scipy.
- [x] Multi-threading for UI and Server.
- [x] Real-time config updates without restarting (for most parameters).

## 6. Configuration & Customization
- [x] Implement Color Profiles system (separate file `colors.yaml`).
- [x] Ensure all parameters are editable via client and saved to config file.

## 7. Testing & Optimization
- [x] Add unit tests for FFT and processing logic.
- [x] Optimize performance using efficient array operations.

## 8. Git Management
- [x] Pushed changes frequently with descriptive commit messages.
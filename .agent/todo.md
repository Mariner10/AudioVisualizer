# Task List - AudioVisualizer Phase 2 (Enhancements)

## 1. Color System Improvements
- [ ] Implement color based on amplitude in `TerminalVisualizer`.
- [ ] Respect color profile `type` (solid, frequency, amplitude) in `TerminalVisualizer`.
- [ ] Sync color profiles to Browser frontend.
- [ ] Implement color profiles in Browser frontend (Canvas rendering).

## 2. Audio Processing Enhancements
- [ ] Implement a more robust "Modulation" system (Carrier frequency adjustment, etc.).
- [ ] Improve Pitch Shifting (maybe basic Phase Vocoder if possible, or just better interpolation).
- [ ] Add "Stereo" support (currently it seems to be mono-mixed).

## 3. UI/UX Improvements
- [ ] Add more info to the Terminal Settings Menu.
- [ ] Improve Browser UI (better sliders, color profile selector).
- [ ] Add a "File Selector" for the browser if in file mode.

## 4. Documentation & Maintenance
- [ ] Update README.md with current features and instructions.
- [ ] Add more comprehensive tests for audio transformations.

## 5. Efficiency & Performance
- [ ] Make neccesary changes to remove almost all latency from playback / listening.
- [ ] Research whether or not threading / multiprocessing the calculations ahead of when they should be played would be beneficial.
- [ ] Develop a caching system for the audio too play, generate ahead when resources are free - re-generating with as little interuptions as possible when LIVE settings are changed.

## 6. Configuration & Customization
- [ ] Implement Color Profiles system (separate file, highly customizable).
- [ ] Ensure all parameters are editable via client and saved to config file.

## 7. Testing & Optimization
- [ ] Add unit tests for FFT and processing logic.
- [ ] Optimize performance using multiprocessing where necessary.

## 8. Git Management
- [ ] Use feature branches and push changes frequently.

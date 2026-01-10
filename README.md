The goal of this project is to create a vastly customizable audio tool with visualizer than can both utilize the live microphone as well as input MP3, WAV, FLAC files and display a
configurable audio visualization display. 

- In the case of the live microphone, it shows the visualizer, listens to the system microphone and re-outputs the audio it captured. 
- In the case of an input file, it should show the visualizer AND play the file to the defualt system audio output.

- All parameters of this program should be configurable within a single editable JSON, TOML, YAML, etc... file. This parameter file needs to be editable via the viewer / client.

The visualizer should utilize a certain type of Fourier Transform to decode the audio by splitting the audio into discrete sections and analyizing them within a certain range of freqencies. These parameters should be adjustable.

It is supported and encouraged to utilize multiprocessing/multithreading where neccesary in order to make the program as efficent/fast as possible in order to be as real-time as it can be.

The visualizer should have the following customizable components for both the microphone and file input methods:

- Display type - (i.e smooth line, bar chart, bi-directional bar chart) it should be simple to add more of these - so make it modular.
- Display color - (i.e solid color, fading colors, color based on frequency, color based on amplitude) these color profiles should be definable in a separate file and read into the program, they should be easily written and highly customizable. These parameters should be within the aforementioned single editable config file.
- Audio live editing - Whilst performing the transformations to the audio there needs to be capability to both raise/lower the frequency, volume, timescale (slowing down/speeding up the audio), these should be able to be changed on-the-fly mid playback.
- Future goal: modulation of signal in real time with either a carrier frequency or separate audio file.

There should be multiple ways to see/hear the visualizer, so there needs to be a standardized method of output so that multiple 'frontends' can display / play it properly.

- Terminal: The visualizer should use correctly oriented Braile dots to display the visualizer in the terminal (it should look similarly to the btop tool resource monitors). The terminals viewer needs to live scale and adjust accordingly to the size of the terminal window. It should output audio to the a selectable output. It should have a settings menu which allows the user to navigate and edit the programs settings. ALL live settings should be able to made edits to without entering the settings menu with certain keys.
- Browser:  The browser should utilize it's enhanced rendering capabilites to allow smoother, more colorful, and overall higher quality visuals. It should also have a settings menu which allows both the LIVE audio edits, as well as the others.

The project should be tracked and updated in the git repo, and pushed with gh. It is encouraged to utilize feature branches, merging when ready, and only leaving the repository in a working state at any given time.
Testing needs to be done to ensure that the calculations are working correctly, so there needs to be tests that are written and performed.


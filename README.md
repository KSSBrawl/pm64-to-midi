# pm64-to-midi
 Tool to convert music data from Paper Mario to MIDI

# Dependencies
 This script depends on the [Mido](https://github.com/mido/mido) Python library.

# Usage
 The expected BGM format is raw BGM data files that can be obtained with the Paper Mario decompilation project which you can find [here](https://github.com/pmret/papermario).

 To get the BGM files, set up that repository per the instructions provided there, and then you can find the BGM files in /assets/[version]/bgm

 Once you have the BGM files, run the script like so:

```
python3 pm64_to_midi.py bgm_file segment_id midi_file
```
 where `segment_id` is a number from 0-3.

# Current completion status
 There are some features that will be added in the future, including:
* Only outputting the number of tracks the song uses (I was too lazy to do this for the initial version)
* Support for loops
* Support for MIDI format 0

Additionally, there are currently several BGM commands that can be translated to MIDI are not implemented. These are:
* Master volume
* Master volume fade
* Master tuning
* Tempo fade
* Track tremolo
* Track tremolo speed
* Track tremolo time
* Track tremolo stop
* Track volume fade

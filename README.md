# pm64-to-midi
 Tool to convert music data from Paper Mario to MIDI

# Rationale
 I want to restore some of the songs from Paper Mario using the actual synth the instruments were sampled off of, and N64SoundBankTool doesn't support the commands I want it to so I made this :T

# Dependencies
 This script depends on the [Mido](https://github.com/mido/mido) Python library.

# Usage
 The expected BGM format is raw BGM data files that can be obtained with the Paper Mario decompilation project which you can find [here](https://github.com/pmret/papermario).

 To get the BGM files, set up that repository per the instructions provided there, and then you can find the BGM files in /assets/[version]/bgm

 Once you have the BGM files, run the script like so:

```
python3 pm64_to_midi.py [-h] [-t] -i bgm_file -s segment -o midi_file

```

# Current completion status
 There are some features that will be added in the future, including:
* More robust error handling
* Support for loops
* Support for MIDI format 0

Additionally, there are currently several BGM commands that can be translated to MIDI that are not implemented. These are:
* Master volume
* Master volume fade
* Master tuning
* Track tremolo
* Track tremolo speed
* Track tremolo time
* Track tremolo stop
* Track volume fade

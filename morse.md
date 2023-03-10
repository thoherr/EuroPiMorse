# Euro Pi Morse - Morse code sequences generator for Euro Pi

author: Thomas Herrmann (github.com/thoherr)

date: 2023-02-19

labels: sound creation, gate

## Overview

This script creates the gate (and CV) signals for the morse code of a given/configurable string.

Currently the available strings are created as a default array in the program. They are stored with the script
state, so it is possible to edit them by connecting to the EuroPI and editing the configuration file in the root
directory of the EuroPI.

## Operation

In order to work, the script requires a clock signal. This has to be provided via the Digital Input (din).

The script has several modes of operation. The main modes are *RUNNING* and *PAUSED*. The initial mode is *PAUSED*.

In order to change parameter values, the paramater adjustment modes *ADJUST CV* and *ADJUST TEXT* can be used.
When saving or discarding changes in adjustment modes, the script returns to the previous main mode.

The morsed text can be changed manually (see Controls) or via CV input. The text is selected by the percentage of
the input voltage. If this value is below 0.1% of the input voltage range, the input is ignored.

### Inputs

| **Port** | **Description** |
|----------|-----------------|
| din | clock (one DIT) |
| ain | select morsed text by index into available texts (if above threshold of 0.1%) |

### Controls

#### Knobs

| **Knob** | **Current mode** | **Function** |
|----------|------------------|--------------|
| k1 | ADJUST CV | select CV for pitch output |
| k1 | ADJUST TEXT | select text entry from list of available texts |
| k2 | ADJUST CV or ADJUST TEXT | not used |

#### Buttons

| **Button** | **Press** | **Current mode** | **Function** |
|------------|-----------|------------------|--------------|
| b1 | klick | PAUSED |  Switch to RUNNING mode and start morsing the currently selected text |
| b1 | klick | RUNNING  | Switch to PAUSED mode (stop mording) |
| b1 | > 1 sec | PAUSED or RUNNING | Switch to ADJUST CV |
| b1 | klick | ADJUST CV | Save currently selected CV and return to main mode |
| b1 | klick | ADJUST TEXT | Save currently selected text and return to main mode |
| b2 | klick | PAUSED or RUNNING | Switch to ADJUST TEXT |
| b2 | klick | ADJUST CV | Restore old CV value and return to main mode |
| b2 | klick | ADJUST TEXT | Restore old CV value and return to main mode |

### Outputs

| **Port** | **Description** |
|----------|-----------------|
| cv1 | morse signal (gate) |
| cv2 | end of character (gate) |
| cv3 | end of word (gate) |
| cv4 | morse signal (CV) |
| cv5 | end of sequence (gate) |
| cv6 | morse code is sent, i.e. script is in running mode (gate) |

## Background information

### Morse code timing

One clock trigger is interpreted as a so called *DIT* by the script, i.e. one short morse signal, which also
defines the time of the silence between individual signals.

A long signal, called *DAH*, lasts for 3 *DIT*s, i.e. 3 clock cycles, which also defines the time of silence
between individual characters.

Last not least, the end of a word is coded by a silence lasting 7 *DIT*s.

More details can be found at the
[english](https://en.wikipedia.org/wiki/Morse_code#Representation,_timing,_and_speeds) or the
[german](https://de.wikipedia.org/wiki/Morsecode#Zeitschema_und_Veranschaulichung)
Wikipedia page about Morse code timing.

### Morse code pitch

*Morse code is often at a frequency between 600 and 800 Hz*, stated in
[this blog article](https://www.johndcook.com/blog/2022/02/25/morse-code-in-musical-notation).

Therefore, the range of our CV is between 3.25 V, which is roughly Eb3 (311 Hz) and
5.0 V, which is roughly C5 (1047 Hz), with a default of 4.333 V, which is roughly E4 (659 Hz).

## Enhancements / Ideas

* Make texts editable (i.a. add new entries, delete entries and edit entries; editor would could enter charaters by knobs like the UI of NetFlix or older car navigation systems)
* Input to change morsed text (via *ain* ?)
* Input to start and stop sequence (this could be done already by patching the mandatory clock signal)

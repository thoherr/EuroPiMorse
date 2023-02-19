"""
Euro Pi Morse - Morse code sequences generator for Euro Pi
author: Thomas Herrmann (github.com/thoherr)
date: 2023-02-19
labels: sound creation, gate

This script creates the gate signals for the morse code of a given/configurable string.

Description of UI elements is preliminary!

din: clock (one DIT)
ain: not used (probably selection of words/sentences generated some day)

k1: select speed ??
k2: select text

b1: start/stop morse code (on/off) in primary mode,
    selection in menu mode
b2: switch to menu mode

cv1: morse signal (gate)
cv2: not used
cv3: not used
cv4: end of sequence
cv5: not used
cv6: not used

"""

from time import sleep
from utime import ticks_diff, ticks_ms
from europi import oled
from europi_script import EuroPiScript

VERSION = "0.1"

# UI timing

SAVE_STATE_INTERVAL = 5000
SHORT_PRESSED_INTERVAL = 600  # feels about 1 second
LONG_PRESSED_INTERVAL = 2400  # feels about 4 seconds

# Morse code timing
# See https://en.wikipedia.org/wiki/Morse_code#Representation,_timing,_and_speeds or
#     https://de.wikipedia.org/wiki/Morsecode#Zeitschema_und_Veranschaulichung

DIT_LEN = 1
DAH_LEN = 3
SYM_GAP = DIT_LEN
LETTER_GAP = 3 * DIT_LEN
WORD_GAP = 7 * DIT_LEN

# Morse code encoding
DIT = "."
DAH = "_"
MORSE_CODE = {
    # latin letters
    "A": "._",
    "B": "_...",
    "C": "_._.",
    "D": "_..",
    "E": ".",
    "F": ".._.",
    "G": "__.",
    "H": "....",
    "I": "..",
    "J": ".___",
    "K": "_._",
    "L": "._..",
    "M": "__",
    "N": "_.",
    "O": "___",
    "P": ".__.",
    "Q": "__._",
    "R": "._.",
    "S": "...",
    "T": "_",
    "U": ".._",
    "V": "..._",
    "W": ".__",
    "X": "_.._",
    "Y": "_.__",
    "Z": "__..",
    # digits
    "1": ".____",
    "2": "..___",
    "3": "...__",
    "4": "...._",
    "5": ".....",
    "6": "_....",
    "7": "__...",
    "8": "___..",
    "9": "____.",
    "0": "_____",
    # umlauts and ligatures - not imlemented yet
    # symbols
    ".": "._._._",  # AAA
    ",": "__..__",  # MIM
    ":": "___...",  # OS
    ";": "_._._.",  # NNN
    "?": "..__..",  # IMI
    "!": "_._.__",
    "-": "_...._",  # BA
    "_": "..__._",  # UK
    "(": "_.__.",   # KN
    ")": "_.__._",  # KK
    "'": ".____.",  # JN
    "=": "_..._",   # BT
    "+": "._._.",   # AR
    "/": "_.._.",   # DN
    "@": ".__._.",  # AC
    "\"": "._.._.",
}


class Morse(EuroPiScript):
    initial_state = "HELLO WORLD"
    state_saved = True

    def __init__(self):
        super().__init__()

        oled.contrast(0)

        self.load_state()

        self.display_data_changed = True

    @classmethod
    def display_name(cls):
        return "Morse code"

    def save_state(self):
        if self.state_saved or self.last_saved() < SAVE_STATE_INTERVAL:
            return
        # TODO: Implement
        self.save_state_str("NOT IMPLEMENTED")
        self.state_saved = True

    def load_state(self):
        state = self.load_state_str()
        if state:
            # TODO: Implement
            pass

    def update_cvs(self):
        pass

    def update_display(self):
        if self.display_data_changed:
            oled.fill(0)

            # TODO: Implement

            oled.show()

            display_data_changed = False

    def main(self):
        oled.centre_text(f"EuroPi\nMorse Code\n{VERSION}")
        sleep(1)
        while True:
            self.update_cvs()
            self.update_display()
            self.save_state()
            sleep(0.01)


# Main script execution
if __name__ == "__main__":
    script = Morse()
    script.main()

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
from europi import oled, din
from europi_script import EuroPiScript

VERSION = "0.1"

# UI timing

SAVE_STATE_INTERVAL = 5000
# SHORT_PRESSED_INTERVAL = 600  # feels about 1 second
# LONG_PRESSED_INTERVAL = 2400  # feels about 4 seconds

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

class MorseCharacter:
    def __init__(self, char, sequence):
        self.char = char
        self.sequence = sequence
        self.duration = DIT_LEN * (len(self.sequence) - 1)
        for c in sequence:
            self.duration = self.duration + (DIT_LEN if c == DIT else DAH_LEN)


MORSE_CHARACTERS = [
    # latin letters
    MorseCharacter("A", "._"),
    MorseCharacter("B", "_..."),
    MorseCharacter("C", "_._."),
    MorseCharacter("D", "_.."),
    MorseCharacter("E", "."),
    MorseCharacter("F", ".._."),
    MorseCharacter("G", "__."),
    MorseCharacter("H", "...."),
    MorseCharacter("I", ".."),
    MorseCharacter("J", ".___"),
    MorseCharacter("K", "_._"),
    MorseCharacter("L", "._.."),
    MorseCharacter("M", "__"),
    MorseCharacter("N", "_."),
    MorseCharacter("O", "___"),
    MorseCharacter("P", ".__."),
    MorseCharacter("Q", "__._"),
    MorseCharacter("R", "._."),
    MorseCharacter("S", "..."),
    MorseCharacter("T", "_"),
    MorseCharacter("U", ".._"),
    MorseCharacter("V", "..._"),
    MorseCharacter("W", ".__"),
    MorseCharacter("X", "_.._"),
    MorseCharacter("Y", "_.__"),
    MorseCharacter("Z", "__.."),
    # digits
    MorseCharacter("1", ".____"),
    MorseCharacter("2", "..___"),
    MorseCharacter("3", "...__"),
    MorseCharacter("4", "...._"),
    MorseCharacter("5", "....."),
    MorseCharacter("6", "_...."),
    MorseCharacter("7", "__..."),
    MorseCharacter("8", "___.."),
    MorseCharacter("9", "____."),
    MorseCharacter("0", "_____"),
    # umlauts and ligatures - not imlemented yet
    # symbols
    MorseCharacter(".", "._._._"),  # AAA
    MorseCharacter(",", "__..__"),  # MIM
    MorseCharacter(":", "___..."),  # OS
    MorseCharacter(";", "_._._."),  # NNN
    MorseCharacter("?", "..__.."),  # IMI
    MorseCharacter("!", "_._.__"),
    MorseCharacter("-", "_...._"),  # BA
    MorseCharacter("_", "..__._"),  # UK
    MorseCharacter("(", "_.__."),   # KN
    MorseCharacter(")", "_.__._"),  # KK
    MorseCharacter("'", ".____."),  # JN
    MorseCharacter("=", "_..._"),   # BT
    MorseCharacter("+", "._._."),   # AR
    MorseCharacter("/", "_.._."),   # DN
    MorseCharacter("@", ".__._."),  # AC
    MorseCharacter("\"", "._.._."),

    MorseCharacter(" ", ""),
]

MORSE_CODE = {mc.char: mc for mc in MORSE_CHARACTERS}

class Morse(EuroPiScript):
    default_text = "HELLO WORLD "
    state_saved = True

    def __init__(self):
        super().__init__()

        oled.contrast(0)

        self.load_state()
        self.tick = 0
        self.duration = len(self.default_text)

        self.display_data_changed = True

        @din.handler
        def din_handler():
            self.clock()

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

    def clock(self):
        self.tick = (self.tick + 1) % self.duration
        self.update_cvs()

    def update_cvs(self):
        pass

    def update_display(self):
        if self.display_data_changed:
            oled.fill(0)

            # TODO: Implement
            c = self.default_text[self.tick]
            mc = MORSE_CODE[c]
            oled.centre_text(f"{mc.char}\n{mc.sequence}\n{mc.duration}")

            oled.show()

            display_data_changed = False

    def main(self):
        oled.centre_text(f"EuroPi\nMorse Code\n{VERSION}")
        sleep(1)
        while True:
            self.update_cvs()
            self.update_display()
            self.save_state()
            sleep(1)
            self.clock()


# Main script execution
if __name__ == "__main__":
    script = Morse()
    script.main()

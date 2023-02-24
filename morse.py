"""
Euro Pi Morse - Morse code sequences generator for Euro Pi
author: Thomas Herrmann (github.com/thoherr)
date: 2023-02-19
labels: sound creation, gate

This script creates the gate signals for the morse code of a given/configurable string.

Description of UI elements is preliminary!

din: clock (one DIT)
ain: not used (probably selection of words/sentences generated some day or start/stop of code)

k1: select CV for pitch output when in CV adjustment mode
    select character to edit when in edit mode
k2: select text character in edit mode

b1: start/stop morse code (switch between running and pause mode) with klick
    enter CV adjustment mode when in running mode and with short (1-3 sec) press
    save selection and return to running mode when in CV adjustment or text selection mode
b2: switch to text selection mode with klick,
    discard changes and return to running mode when in CV adjustment or text selection mode

cv1: morse signal (gate)
cv2: end of character
cv3: end of word
cv4: morse signal (CV)
cv5: end of sequence
cv6: morse code active (running)

"""

from time import sleep
from utime import ticks_diff, ticks_ms
from europi import oled, din, k1, b1, b2, cv1, cv2, cv3, cv4, cv5, cv6
from europi_script import EuroPiScript

VERSION = "0.4"

# UI timing

SAVE_STATE_INTERVAL = 5000
SHORT_PRESSED_INTERVAL = 600  # feels about 1 second
LONG_PRESSED_INTERVAL = 2400  # feels about 4 seconds

# Morse code timing
# See https://en.wikipedia.org/wiki/Morse_code#Representation,_timing,_and_speeds or
#     https://de.wikipedia.org/wiki/Morsecode#Zeitschema_und_Veranschaulichung
DIT_LEN = 1
DAH_LEN = 3 * DIT_LEN
SYM_GAP_LEN = DIT_LEN
EOC_GAP_LEN = 3 * DIT_LEN
EOW_GAP_LEN = 7 * DIT_LEN
EOM_GAP_LEN = 7 * DIT_LEN

# Morse code encoding
DIT = "."
DAH = "_"

# "Morse code is often at a frequency between 600 and 800 Hz"
# (see https://www.johndcook.com/blog/2022/02/25/morse-code-in-musical-notation)
# a good value is e.g. PITCH_CV = 4.33, which is roughly E4 (659 Hz)
# So we make the pitch adjustable with K1 and give it some variablilty
DEFAULT_PITCH_CV = 4.33  # roughly E4 (659 Hz)
MIN_PITCH_CV = 3.25  # roughly Eb3 (311 Hz)
MAX_PITCH_CV = 5.0  # roughly C5 (1047 Hz)
PITCH_CV_STEPS = int((MAX_PITCH_CV - MIN_PITCH_CV) * 12)

# Word separator
EOW_CHAR = " "

# Output channels
GATE_OUT = cv1
PITCH_OUT = cv4
EOC_OUT = cv2
EOW_OUT = cv3
EOM_OUT = cv5
RUNNING_OUT = cv6


class MorseCharacter:
    def __init__(self, char, sequence):
        self.char = char
        self.sequence = sequence
        if char != "EOC" and char != "EOM":
            self.sequence = " ".join(self.sequence)
        self.gates = []
        for sym in self.sequence:
            self.gates.extend(
                [True] * DIT_LEN
                if sym == DIT
                else [True] * DAH_LEN
                if sym == DAH
                else [False] * SYM_GAP_LEN
            )
        self.duration = len(self.gates)
        # print(f"{self.char} -> {self.gates}")


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
    MorseCharacter("(", "_.__."),  # KN
    MorseCharacter(")", "_.__._"),  # KK
    MorseCharacter("'", ".____."),  # JN
    MorseCharacter("=", "_..._"),  # BT
    MorseCharacter("+", "._._."),  # AR
    MorseCharacter("/", "_.._."),  # DN
    MorseCharacter("@", ".__._."),  # AC
    MorseCharacter('"', "._.._."),
]

MORSE_CODE = {mc.char: mc for mc in MORSE_CHARACTERS}
EOC_MC = MorseCharacter("EOC", " " * EOC_GAP_LEN)
EOW_MC = MorseCharacter("EOW", " " * EOW_GAP_LEN)
EOM_MC = MorseCharacter("EOM", " " * EOM_GAP_LEN)

DEFAULT_TEXTS = [
    "HELLO WORLD",
    "TEMPUS FUGIT",
    "SOS",
    "HELP",
    "EVE",
    "OMNE VIVUM EX VIVO",
    "THAT'S ONE SMALL STEP FOR A MAN, ONE GIANT LEAP FOR MANKIND.",
]


class State:
    def __init__(self, texts):
        self.texts = texts
        self.text_index = 0
        self.pitch_cv = DEFAULT_PITCH_CV
        self.update_display = False
        self.saved = True


class Mode:
    def __init__(self, name, state):
        self.name = name
        self.state = state
        self.display_data_changed = True

    def clock(self):
        pass

    def b1_klick(self):
        return self

    def b1_short_press(self):
        return self

    def b1_long_press(self):
        return self

    def b2_klick(self):
        return self

    def b2_short_press(self):
        return self

    def b2_long_press(self):
        return self

    def update_state(self):
        pass

    def update_display(self):
        if self.display_data_changed:
            oled.fill(0)
            self.paint_display()
            oled.show()
            self.display_data_changed = False


class Running(Mode):
    def __init__(self, state):
        super().__init__("RUNNING", state)
        self.reset_clock()

    def b1_klick(self):
        self.display_data_changed = True
        return Paused(self.state)

    def b1_short_press(self):
        self.display_data_changed = True
        return ChangeCV(self)

    def b2_klick(self):
        self.display_data_changed = True
        return ChangeText(self)

    def cache_mc_data(self):
        self.dits_in_char = self.mc.duration
        self.gates = self.mc.gates

    def reset_clock(self):
        self.character_tick = -1
        self.dit_tick = -1
        self.dits_in_char = 1
        self.mc = EOC_MC
        self.cache_mc_data()

    def clock(self):
        self.dit_tick = (self.dit_tick + 1) % self.dits_in_char
        if self.dit_tick == 0:
            if self.mc != EOM_MC and self.character_tick + 1 == len(
                self.state.texts[self.state.text_index]
            ):
                self.mc = EOM_MC
            elif (
                self.character_tick + 1 < len(self.state.texts[self.state.text_index])
                and self.state.texts[self.state.text_index][self.character_tick + 1]
                == EOW_CHAR
            ):
                self.character_tick = self.character_tick + 1
                self.mc = EOW_MC
            elif self.mc == EOC_MC or self.mc == EOW_MC or self.mc == EOM_MC:
                self.character_tick = (self.character_tick + 1) % len(
                    self.state.texts[self.state.text_index]
                )
                self.mc = MORSE_CODE[
                    self.state.texts[self.state.text_index][self.character_tick]
                ]
            else:
                self.mc = EOC_MC
            self.cache_mc_data()
        self.update_cvs()
        self.display_data_changed = True

    def update_cvs(self):
        gate = self.gates[self.dit_tick]
        GATE_OUT.value(gate)
        PITCH_OUT.voltage(self.state.pitch_cv)
        EOC_OUT.value(
            (self.mc == EOC_MC or self.mc == EOW_MC or self.mc == EOM_MC)
            and self.dit_tick < EOC_GAP_LEN
        )
        EOW_OUT.value(
            (self.mc == EOW_MC or self.mc == EOM_MC and self.dit_tick < EOW_GAP_LEN)
        )
        EOM_OUT.value(self.mc == EOM_MC)
        RUNNING_OUT.on()

    def paint_display(self):
        oled.centre_text(
            f"{self.state.texts[self.state.text_index]}\n{self.mc.sequence}\n{self.mc.char} {'*' if self.gates[self.dit_tick] else ' '}"
        )


class ChangeCV(Mode):
    def __init__(self, parent):
        super().__init__("CHANGE_CV", parent.state)
        self.parent = parent
        self.old_cv = self.state.pitch_cv
        self.current_cv = MIN_PITCH_CV + k1.range(PITCH_CV_STEPS + 1) / 12

    def b1_klick(self):
        self.display_data_changed = True
        return self.parent

    def b2_klick(self):
        self.state.pitch_cv = self.old_cv
        self.display_data_changed = True
        return self.parent

    def clock(self):
        self.parent.clock()

    def update_cvs(self):
        self.parent.update_cvs()

    def update_state(self):
        knob_cv = MIN_PITCH_CV + k1.range(PITCH_CV_STEPS + 1) / 12
        if knob_cv != self.current_cv:
            self.current_cv = knob_cv
            self.state.pitch_cv = knob_cv
            self.display_data_changed = True

    def paint_display(self):
        oled.centre_text(
            f"{self.state.text[self.state.text_index]}\nCUR CV {self.old_cv:1.2f}\nNEW CV {self.state.pitch_cv:1.2f}"
        )


class ChangeText(Mode):
    def __init__(self, parent):
        super().__init__("CHANGE_TEXT", parent.state)
        self.parent = parent
        self.new_index = self.state.text_index
        self.current_index = k1.range(len(self.state.texts))

    def b1_klick(self):
        self.state.text_index = self.new_index
        self.parent.reset_clock()
        self.display_data_changed = True
        return self.parent

    def b2_klick(self):
        self.display_data_changed = True
        return self.parent

    def clock(self):
        self.parent.clock()

    def update_cvs(self):
        self.parent.update_cvs()

    def update_state(self):
        index = k1.range(len(self.state.texts))
        if index != self.current_index:
            self.current_index = index
            self.new_index = index
            self.display_data_changed = True

    def paint_display(self):
        oled.centre_text(
            f"{self.state.texts[self.state.text_index]}\n-->\n{self.state.texts[self.new_index]}"
        )


class Paused(Mode):
    def __init__(self, state):
        super().__init__("PAUSED", state)

    def b1_klick(self):
        self.display_data_changed = True
        return Running(self.state)

    def update_cvs(self):
        cv1.off()
        cv2.off()
        cv3.off()
        cv4.off()
        cv5.off()
        cv6.off()

    def paint_display(self):
        oled.centre_text(f"{self.state.texts[self.state.text_index]}\n\n")
        oled.fill_rect(59, 18, 4, 8, 1)
        oled.fill_rect(65, 18, 4, 8, 1)


class Morse(EuroPiScript):
    state_saved = True

    def __init__(self):
        super().__init__()

        oled.contrast(0)

        self.load_state()

        self.mode = Paused(self.state)

        @din.handler
        def din_handler():
            self.mode.clock()

        @b1.handler_falling
        def b1_handler():
            time_pressed = ticks_diff(ticks_ms(), b1.last_pressed())
            if time_pressed >= LONG_PRESSED_INTERVAL:
                self.mode = self.mode.b1_long_press()
            elif time_pressed >= SHORT_PRESSED_INTERVAL:
                self.mode = self.mode.b1_short_press()
            else:
                self.mode = self.mode.b1_klick()

        @b2.handler_falling
        def b2_handler():
            time_pressed = ticks_diff(ticks_ms(), b2.last_pressed())
            if time_pressed >= LONG_PRESSED_INTERVAL:
                self.mode = self.mode.b2_long_press()
            elif time_pressed >= SHORT_PRESSED_INTERVAL:
                self.mode = self.mode.b2_short_press()
            else:
                self.mode = self.mode.b2_klick()

    @classmethod
    def display_name(cls):
        return "Morse code"

    def save_state(self):
        if self.state.saved or self.last_saved() < SAVE_STATE_INTERVAL:
            return
        self.state.save_state_str(self.state.texts)
        # TODO: Save current text index
        self.state.saved = True

    def load_state(self):
        # TODO: Load current text index
        state_str = self.load_state_str()
        if state_str:
            self.state = State(state_str.splitlines())
        else:
            self.state = State(DEFAULT_TEXTS)

    def main(self):
        oled.centre_text(f"EuroPi\nMorse Code\n{VERSION}")
        sleep(1)
        while True:
            self.mode.update_state()
            self.mode.update_display()
            self.save_state()
            sleep(0.01)


# Main script execution
if __name__ == "__main__":
    script = Morse()
    script.main()

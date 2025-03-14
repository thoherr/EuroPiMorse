"""
Euro Pi Morse - Morse code sequences generator for Euro Pi
author: Thomas Herrmann (github.com/thoherr)

For user documentation of this script see file morse.md

"""

from time import sleep
from utime import ticks_diff, ticks_ms
from europi import (
    oled,
    CHAR_WIDTH,
    CHAR_HEIGHT,
    din,
    ain,
    k1,
    b1,
    b2,
    cv1,
    cv2,
    cv3,
    cv4,
    cv5,
    cv6,
)
from europi_script import EuroPiScript

VERSION = "0.6"

# UI timing

SAVE_STATE_INTERVAL = 5000
SHORT_PRESSED_INTERVAL = 600  # feels about 1 second
LONG_PRESSED_INTERVAL = 2400  # feels about 4 seconds

BLINK_MS = 700
BLINK_RATIO = 2

# Threshold for analog input to specify text index
AIN_TEXTCHANGE_THRESHOLD = 0.1

# Display properties
OLED_CHARS_PER_LINE = int(oled.width / CHAR_WIDTH)

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
DEFAULT_PITCH_CV = 4.333  # roughly E4 (659 Hz)
MIN_PITCH_CV = 3.250  # roughly Eb3 (311 Hz)
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
    # umlauts and ligatures - not fully imlemented
    MorseCharacter("Á", ".__._"),
    MorseCharacter("Ä", "._._"),
    MorseCharacter("É", ".._.."),
    MorseCharacter("Ñ", "__.__"),
    MorseCharacter("Ö", "___."),
    MorseCharacter("Ü", "..__"),
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
ERROR_MC = MorseCharacter("ERROR", "." * 8)

DEFAULT_STATE = [
    f"{DEFAULT_PITCH_CV}",
    "0",
    "HELLO WORLD",
    "TEMPUS FUGIT",
    "SOS",
    "HELP",
    "EVE",
    "OMNE VIVUM EX VIVO",
    "THAT'S ONE SMALL STEP FOR A MAN, ONE GIANT LEAP FOR MANKIND.",
    "IM ANFANG WAR DAS WORT!",
    "IM ANFANG WAR DER SINN.",
    "IM ANFANG WAR DIE KRAFT!",
    "IM ANFANG WAR DIE THAT!",
]


class State:
    def __init__(self, state_str):
        if state_str:
            lines = state_str.splitlines()
        else:
            lines = DEFAULT_STATE
        self._pitch_cv = float(lines[0])
        self._text_index = int(lines[1])
        self.texts = lines[2:]
        self.saved = True

    @property
    def pitch_cv(self):
        return self._pitch_cv

    @pitch_cv.setter
    def pitch_cv(self, value):
        self._pitch_cv = value
        self.saved = False

    @property
    def text_index(self):
        return self._text_index

    @text_index.setter
    def text_index(self, value):
        self._text_index = value
        self.saved = False

    def serialize(self):
        return f"{self._pitch_cv:1.3f}\n{self._text_index}\n" + "\n".join(self.texts)


class Mode:
    def __init__(self, name, state):
        self.name = name
        self.state = state
        self.blink_on = False

    def current_text(self):
        return self.state.texts[self.state.text_index]

    def clock(self):
        pass

    def reset_clock(self):
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

    def blink_triggered(self, blink_state):
        pass

    def blink(self):
        on = (ticks_ms() % BLINK_MS) < (BLINK_MS / BLINK_RATIO)
        if self.blink_on != on:
            self.blink_on = on
            self.blink_triggered(on)

    def update_state(self):
        self.blink()

    def paint_centered_text(self, line, content):
        x = int((oled.width - (len(content) * CHAR_WIDTH)) / 2)
        y = int((line * (CHAR_HEIGHT + 1)) + 1)
        oled.text(f"{content}", x, y)

    def paint_display(self):
        self.paint_titleline()
        self.paint_content()

    def update_display(self):
        oled.fill(0)
        self.paint_display()
        oled.show()


class MainMode(Mode):
    def __init__(self, name, state):
        super().__init__(name, state)

    def b1_short_press(self):
        return ChangeCV(self)

    def b2_klick(self):
        return ChangeText(self)


class Paused(MainMode):
    def __init__(self, state):
        super().__init__("PAUSED", state)
        self.all_outputs_off()
        self.display_text_offset = 0
        self.number_of_overflow_characters = (
            len(self.current_text()) - OLED_CHARS_PER_LINE
        )

    def b1_klick(self):
        return Running(self.state)

    def clock(self):
        pass

    def all_outputs_off(self):
        GATE_OUT.off()
        PITCH_OUT.off()
        EOC_OUT.off()
        EOW_OUT.off()
        EOM_OUT.off()
        RUNNING_OUT.off()

    def blink_triggered(self, blink_state):
        if blink_state and self.number_of_overflow_characters > 0:
            self.display_text_offset = (self.display_text_offset + 1) % (
                self.number_of_overflow_characters + 1
            )

    def paint_titleline(self):
        self.paint_centered_text(
            0,
            self.current_text()[
                self.display_text_offset : self.display_text_offset
                + OLED_CHARS_PER_LINE
            ],
        )

    def paint_content(self):
        if self.blink_on:
            oled.fill_rect(59, 18, 4, 8, 1)
            oled.fill_rect(65, 18, 4, 8, 1)


class Running(MainMode):
    def __init__(self, state):
        super().__init__("RUNNING", state)
        self.reset_clock()
        RUNNING_OUT.on()

    def b1_klick(self):
        return Paused(self.state)

    def cache_text_and_mc_data(self):
        max_index = len(self.current_text()) - 1
        self.prefix = self.current_text()[0 : self.character_tick]
        self.current_char = (
            self.current_text()[self.character_tick]
            if self.character_tick <= max_index
            else ""
        )
        self.postfix = (
            self.current_text()[self.character_tick + 1 :]
            if self.character_tick < max_index
            else ""
        )
        self.dits_in_char = self.mc.duration
        self.gates = self.mc.gates
        self.gate = False

    def reset_clock(self):
        self.character_tick = -1
        self.dit_tick = -1
        self.dits_in_char = 1
        self.mc = EOC_MC
        self.cache_text_and_mc_data()

    def read_analogue_input(self):
        analog_percent = ain.percent()
        if analog_percent > AIN_TEXTCHANGE_THRESHOLD:
            self.state.text_index = int(
                (analog_percent - AIN_TEXTCHANGE_THRESHOLD) * len(self.state.texts)
            )

    def handle_end_of_character(self):
        nextctick = self.character_tick + 1
        if self.mc != EOM_MC and nextctick == len(self.current_text()):
            self.mc = EOM_MC
        elif (
            nextctick < len(self.current_text())
            and self.current_text()[nextctick] == EOW_CHAR
        ):
            self.character_tick = nextctick
            self.mc = EOW_MC
        elif self.mc == EOC_MC or self.mc == EOW_MC or self.mc == EOM_MC:
            self.character_tick = nextctick % len(self.current_text())
            if self.character_tick == 0:
                self.read_analogue_input()
            self.mc = MORSE_CODE[self.current_text()[self.character_tick]]
        else:
            self.mc = EOC_MC
        self.cache_text_and_mc_data()

    def clock(self):
        self.dit_tick = (self.dit_tick + 1) % self.dits_in_char
        if self.dit_tick == 0:
            self.handle_end_of_character()
        self.gate = self.gates[self.dit_tick]
        self.update_cvs()

    def update_cvs(self):
        GATE_OUT.value(self.gate)
        PITCH_OUT.voltage(self.state.pitch_cv)
        EOC_OUT.value(
            (self.mc == EOC_MC or self.mc == EOW_MC or self.mc == EOM_MC)
            and self.dit_tick < EOC_GAP_LEN
        )
        EOW_OUT.value(
            (self.mc == EOW_MC or self.mc == EOM_MC and self.dit_tick < EOW_GAP_LEN)
        )
        EOM_OUT.value(self.mc == EOM_MC)

    def paint_titleline(self):
        x_center = int((oled.width - (len(self.current_char) * CHAR_WIDTH)) / 2)
        x_for_prefix = len(self.prefix) * CHAR_WIDTH
        x_current_char = min(max(x_center, x_for_prefix), oled.width - CHAR_WIDTH)
        y = 1
        if len(self.prefix) > 0:
            oled.text(f"{self.prefix}", x_current_char - x_for_prefix, y)
        if self.gate or self.mc == EOM_MC:
            oled.text(f"{self.current_char}", x_current_char, y)

    def paint_content(self):
        self.paint_centered_text(1, self.mc.sequence)
        if self.mc == EOW_MC or self.mc == EOM_MC:
            self.paint_centered_text(2, self.mc.char)


class SubMode(Mode):
    def __init__(self, name, main_mode):
        super().__init__(name, main_mode.state)
        self.main_mode = main_mode

    def clock(self):
        self.main_mode.clock()

    def update_state(self):
        super().update_state()
        self.main_mode.update_state()

    def update_cvs(self):
        self.main_mode.update_cvs()

    def paint_titleline(self):
        self.main_mode.paint_titleline()


class ChangeCV(SubMode):
    def __init__(self, main_mode):
        super().__init__("CHANGE_CV", main_mode)
        self.old_cv = self.state.pitch_cv
        self.current_cv = MIN_PITCH_CV + k1.range(PITCH_CV_STEPS + 1) / 12

    def b1_klick(self):
        return self.main_mode

    def b2_klick(self):
        if self.state.pitch_cv != self.old_cv:
            self.state.pitch_cv = self.old_cv
        return self.main_mode

    def update_state(self):
        super().update_state()
        knob_cv = MIN_PITCH_CV + k1.range(PITCH_CV_STEPS + 1) / 12
        if knob_cv != self.current_cv:
            self.current_cv = knob_cv
            self.state.pitch_cv = knob_cv
            self.update_cvs()

    def paint_content(self):
        self.paint_centered_text(1, f"CUR CV {self.old_cv:1.3f}")
        self.paint_centered_text(2, f"NEW CV {self.state.pitch_cv:1.3f}")


class ChangeText(SubMode):
    def __init__(self, main_mode):
        super().__init__("CHANGE_TEXT", main_mode)
        self.current_index = k1.range(len(self.state.texts))
        self.new_index = self.state.text_index
        self.display_text_offset = 0
        self.number_of_overflow_characters = (
            len(self.state.texts[self.new_index]) - OLED_CHARS_PER_LINE
        )

    def b1_klick(self):
        self.state.text_index = self.new_index
        self.main_mode.reset_clock()
        return self.main_mode

    def b2_klick(self):
        return self.main_mode

    def update_state(self):
        super().update_state()
        index = k1.range(len(self.state.texts))
        if index != self.current_index:
            self.current_index = index
            self.new_index = index
            self.number_of_overflow_characters = (
                len(self.state.texts[self.new_index]) - OLED_CHARS_PER_LINE
            )
            self.display_text_offset = 0

    def blink_triggered(self, blink_state):
        if blink_state and self.number_of_overflow_characters > 0:
            self.display_text_offset = (self.display_text_offset + 1) % (
                self.number_of_overflow_characters + 1
            )

    def paint_content(self):
        if self.blink_on:
            self.paint_centered_text(1, "-->")
        self.paint_centered_text(
            2,
            self.state.texts[self.new_index][
                self.display_text_offset : self.display_text_offset
                + OLED_CHARS_PER_LINE
            ],
        )


class Morse(EuroPiScript):
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
        self.save_state_str(self.state.serialize())
        self.state.saved = True

    def load_state(self):
        self.state = State(self.load_state_str())

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

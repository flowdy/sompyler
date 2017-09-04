from Sompyler.synthesizer import SAMPLING_RATE

class Measure(object):

    def __init__(
        self, total_ticks, ticks_per_minute,
        lower_stress_level, upper_stress_level
    ):

        self.total_ticks = total_ticks * 1.0

        if isinstance(ticks_per_minute, int):
            ticks_per_minute = (ticks_per_minute, 1)
        else:
            ticks_per_minute = (
                ticks_per_minute[0],
                ticks_per_minute[1] * 1.0 / ticks_per_minute[0]
            )

        if isinstance(lower_stress_level, int):
            self.lower_stress_level = (lower_stress_level, 1)
        else:
            self.lower_stress_level = (
                lower_stress_level[0],
                lower_stress_level[1] * 1.0 / lower_stress_level[0]
            )

        if isinstance(upper_stress_level, int):
            self.upper_stress_level = (upper_stress_level, 1)
        else:
            self.upper_stress_level = (
                upper_stress_level[0],
                upper_stress_level[1] * 1.0 / upper_stress_level[0]
            )

    def __call__(
        self, offset, length,
        stress, chord_stress, max_chord_stress
    ):

        offset /= self.total_ticks
        length /= self.total_ticks

        if int(offset):
            raise RuntimeError("Offset exceeds measure")

        tpm, tpm_factor = self.ticks_per_minute

        offset_s = int(round(SAMPLING_RATE * (tpm * tpm_factor**offset) / 60))

        length_s = int(round(SAMPLING_RATE * (tpm * tpm_factor**length) / 60))

        ls, ls_factor = self.lower_stress
        ls = ls * ls_factor**offset

        us, us_factor = self.upper_stress
        us = us * us_factor**offset

        stress = stress/chord_stress * (
            ls + chord_stress * (us - ls) / max_chord_stress
        )

        return (offset_s, length_s, stress)


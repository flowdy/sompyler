from Sompyler.score.stressor import Stressor

class Measure(object):

    def __init__(
        self, ticks_per_minute, stress_pattern,
        lower_stress_bound, upper_stress_bound
    ):

        self.stressor = Stressor(stress_pattern)

        if isinstance(ticks_per_minute, int):
            ticks_per_minute = (ticks_per_minute, 1)
        elif not isinstance(ticks_per_minute, tuple):
            ticks_per_minute = (
                ticks_per_minute[0],
                ticks_per_minute[1] * 1.0 / ticks_per_minute[0]
            )

        if isinstance(lower_stress_bound, int):
            self.lower_stress_bound = (lower_stress_bound, 1)
        elif not isinstance(lower_stress_bound, tuple):
            self.lower_stress_bound = (
                lower_stress_bound[0],
                lower_stress_bound[1] * 1.0 / lower_stress_bound[0]
            )

        if isinstance(upper_stress_bound, int):
            self.upper_stress_bound = (upper_stress_bound, 1)
        elif not isinstance(upper_stress_bound, tuple):
            self.upper_stress_bound = (
                upper_stress_bound[0],
                upper_stress_bound[1] * 1.0 / upper_stress_bound[0]
            )


    def seconds_before_tick( self, tick ):

        offset = 1.0 * tick / self.stressor.cumlen

        if int(offset):
            raise RuntimeError("Offset exceeds measure")

        tpm, tpm_factor = self.ticks_per_minute

        seconds = 60.0 / ( tpm * tpm_factor**offset ) * offset

        return seconds


    def stress_of_tick( self, tick ):

        offset = 1.0 * tick / self.stressor.cumlen

        ls, ls_factor = self.lower_stress_bound
        ls = ls * ls_factor**offset

        us, us_factor = self.upper_stress_bound
        us = us * us_factor**offset

        stress = ls * (us/ls) ** self.stressor.of( round(offset) )
        
        return stress


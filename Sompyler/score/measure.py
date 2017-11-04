from Sompyler.score.stressor import Stressor
from Sompyler.score.chord import Chord

def stress_range(stress):
    if isinstance(stress, int):
        return (lower_stress_bound, 1)
    elif not isinstance(stress, tuple):
        if isinstance(stress, str):
            stress = [ int(x) for x in stress.split("-", 1) ]
        return (
            stress[0],
            stress[1] * 1.0 / stress[0]
        )



class Measure(object):
    __slots__ = ('ticks_per_minute', 'stressor', 'offset',
        'measure_cut', 'lower_stress_bound', 'upper_stress_bound'
    )

    def __init__(
        self, structure, stage, prev
    ):

        meta = structure.pop('_meta', {})

        for prop in (
                'ticks_per_minute', 'stress_pattern',
                'lower_stress_bound', 'upper_stress_bound'
            ):
            setattr(self, prop, meta.get(prop, getattr(prev, prop)))

        
        self.measure_cut = meta['measure_cut'] if 'measure_cut' in meta else 0

        if prev:
            self.offset = prev.offset + prev.stress_before_tick(
                prev.stressor.cumlen - (
                    abs(prev.measure_cut) if prev.measure_cut < 0 else 0
                )
            )
        else:
            self.offset = 0

        self.stressor = Stressor(stress_pattern)

        if isinstance(ticks_per_minute, int):
            self.seconds_per_tick = (60.0 / ticks_per_minute, 1)
        elif not isinstance(ticks_per_minute, tuple):
            if isinstance(ticks_per_minute, str):
                tickets_per_minute = [
                    int(x) for x in ticks_per_minute.split("-", 1)
                ]
            self.seconds_per_tick = (
                60.0 / ticks_per_minute[0],
                ticks_per_minute[0] * 1.0 / ticks_per_minute[1]
            )

        self.lower_stress_bound = stress_range(lower_stress_bound)
        self.upper_stress_bound = stress_range(upper_stress_bound)

        self.structure = structure
        self.voices = stage.voices

    def calculate_seconds_from_ticks( self, offset, length=None ):

        max_offset = self.stressor.cumlen - (
            abs(self.measure_cut)
                if self.measure_cut < 0
                else 0
        )
        if offset > max_offset:
            raise ValueError("Offset exceeding " + max_offset)

        if offset < self.measure_cut > 0:
            raise ValueError("Offset too low")

        exp_div = 1.0 / self.stressor.cumlen
        offset *= exp_div

        spt, spt_factor = self.seconds_per_tick

        def seconds(ticks):
            ticks *= exp_div
            ticks += offset
            return spt * ( ticks if spt_factor == 1 else (
                           ( spt_factor ** ticks   - 1 )
                         / ( spt_factor ** exp_div - 1 )
                       )
                   )

        offset_s = seconds(0)

        if length:
            return offset_s, seconds(length) - offset_s
        else:
            return offset_s


    def stress_of_tick( self, tick ):

        offset = 1.0 * tick / self.stressor.cumlen

        ls, ls_factor = self.lower_stress_bound
        ls = ls * ls_factor**offset

        us, us_factor = self.upper_stress_bound
        us = us * us_factor**offset

        stress = ls * (us/ls) ** self.stressor.of( round(offset) )
        
        return stress

    def __iter__(self):

        # TODO process _meta (stress_pattern, tempo)

        _meta = {}
        for ch_name, ch_data in measure.structure.items():
            # merge general and channel-specific _meta, if any
            ch_meta = ch_data.pop('_meta', {})
            if 'stressor' in ch_meta:
                ch_meta['stressor'] = Stressor( ch_meta['stressor'] )
                if not ch_meta['stressor'].cumlen == self.stressor.cumlen:
                    raise RuntimeError(
                        "Voice bound measure stressor has other length"
                      + " than global measure"
                    )
            else:
                ch_meta['stressor'] = self.stressor

            for prop in 'stressor', 'lower_stress_bound', '_upper_stress_bound':
                if prop in ch_meta:
                    _meta[prop] = ch_meta[prop]

            yield VoiceBoundMeasure(measure, self.voices[ch_name], ch_data, **_meta)


class VoiceBoundMeasure(Measure):
    __slots__ = ('measure', 'channel', 'chords')

    def __init__(
            self, measure, voice, ch_data,
            stressor=None,
            lower_stress_bound=None,
            upper_stress_bound=None
        ):
        self.measure  = measure
        self.voice    = voice
        self.stressor = stressor or measure.stressor
        self.lower_stress_bound = (
            stress_range(lower_stress_bound)
                if lower_stress_bound
                else measure.lower_stress_bound
        )
        self.upper_stress_bound = (
            stress_range(upper_stress_bound)
                if upper_stress_bound
                else measure.upper_stress_bound
        )
        self.chords   = ch_data

    def __iter__(self):

        calc_span = self.measure.calculate_seconds_from_ticks

        for offset, chord in self.chords:

            if not isinstance(chord, list):
                note = chord
                chord = [note]

            yield Chord(
                self.offset, offset, self.voice,
                self.stressor.of(offset),
                calc_span, chord
            )

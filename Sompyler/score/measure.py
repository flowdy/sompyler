import pdb
from math import ceil
from .stressor import Stressor
from .chord import Chord
from ..synthesizer.shape import Shape # realize dynamic tempo and stress

def continuum(some_value):
    if isinstance(some_value, Shape):
        return some_value
    elif isinstance(some_value, int):
        return Shape.from_string(
                str(some_value) + ';1,' + str(some_value)
            )
    else:
        if isinstance(some_value, str):
            if '-' in some_value:
                from_v, to_v = some_value.split('-')
                some_value = from_v + ';1,' + to_v
            return Shape.from_string(some_value)

        else: raise TypeError(
                "continuum must be either int or 'x-y' indication or "
                "shape definition string/object, but it is a "
                + type(some_value)
              )


class Measure:
    __slots__ = (
        'tempo_shape', 'stressor', 'offset', 'length', 'structure',
        'voices', 'measure_cut', 'lower_stress_bound', 'upper_stress_bound'
    )

    def __init__(
            self, structure, stage, previous, cut=None,
            stress_pattern=None, ticks_per_minute=None,
            lower_stress_bound=None, upper_stress_bound=None,
            repeat_unmentioned_voices=False,
        ):

        self.measure_cut = cut or 0

        if not previous and ticks_per_minute is None:
            raise RuntimeError(
                "First measure must have a tempo (meta[ticks_per_minute])"
            )

        if stress_pattern is not None:
            self.stressor = Stressor( stress_pattern.split(";") )
        else:
            self.stressor = previous.stressor

        if ticks_per_minute is None:
            self.tempo_shape = previous.tempo_shape
        else:
            self.tempo_shape = continuum(ticks_per_minute)

        self.lower_stress_bound = (
            continuum(lower_stress_bound).render(
                    self.stressor.cumlen,
                    y_scale=True
                )
                if lower_stress_bound
                else previous.lower_stress_bound
        )

        self.upper_stress_bound = (
            continuum(upper_stress_bound).render(
                    self.stressor.cumlen,
                    y_scale=True
                )
                if upper_stress_bound
                else previous.upper_stress_bound
        )

        self.structure = structure
        self.voices = stage.voices

        self.length = self.stressor.cumlen - abs(self.measure_cut)

        if repeat_unmentioned_voices:
            for voice in previous.structure.keys():
                if voice in structure:
                    continue
                else:
                    structure[voice] = True

        for v_name, voice in structure.items():
            if voice is True:
                structure[v_name] = previous.structure[v_name]

    def __iter__(self):

        for v_name, v_chords in self.structure.items():
            # merge general and voice-specific _meta, if any
            v_meta = v_chords.pop('_meta', {})
            if 'stressor' in v_meta:
                v_meta['stressor'] = Stressor( v_meta['stressor'].split(";") )
                if not v_meta['stressor'].cumlen == self.stressor.cumlen:
                    raise RuntimeError(
                        "Voice bound measure stressor has other length "
                        "than that of the over_all measure"
                    )

            yield VoiceBoundMeasure(
                 self, self.voices[v_name], v_chords, **v_meta
            )

    def get_length_calculator(self, diff):

        cumlen = self.stressor.cumlen
        units = ceil( cumlen / diff )
        
        def tpm_to_seconds(tempo):
            s = 60 * cumlen / (units * tempo)
            return s
        
        tempo_shape = self.tempo_shape
        tempo_profile = self.tempo_shape.render(units, y_scale=tempo_shape.y_max)

        def calc(offset, length):
            offset_i, offset_r = divmod(offset, cumlen / units)
            offset_sum = sum(
                    tpm_to_seconds(i)
                        for i in tempo_profile[0:int(offset_i)]
                ) + offset_r * units / cumlen * tpm_to_seconds(
                    tempo_profile[int(offset_i)]
                )

            end_offset_i, end_offset_r = divmod( 
                    length + offset, cumlen / units
                )
            length_sum = sum(
                    tpm_to_seconds(i)
                        for i in tempo_profile[0:int(end_offset_i)]
                ) + (
                    end_offset_r * units / cumlen
                      * tpm_to_seconds(tempo_profile[int(end_offset_i)])
                      if end_offset_i < len(tempo_profile)
                      else 0
                ) - offset_sum
            return offset_sum, length_sum

        return calc

class VoiceBoundMeasure(Measure):
    __slots__ = ('measure', 'voice', 'chords', 'ticks')

    def __init__(
            self, measure, voice, ch_data,
            stressor=None,
            lower_stress_bound=None,
            upper_stress_bound=None
        ):

        self.measure  = measure
        self.voice    = voice
        self.stressor = stressor or measure.stressor
        self.ticks    = { t for t in ch_data }

        self.lower_stress_bound = (
            continuum(lower_stress_bound).render(
                    self.stressor.cumlen,
                    y_scale=True
                )
                if lower_stress_bound
                else measure.lower_stress_bound
        )

        self.upper_stress_bound = (
            continuum(upper_stress_bound).render(
                    self.stressor.cumlen,
                    y_scale=True
                )
                if upper_stress_bound
                else measure.upper_stress_bound
        )

        self.chords   = ch_data

    def stress_of_tick( self, tick ):

        offset = tick / self.stressor.cumlen
        tick = int(round(tick))

        ls = self.lower_stress_bound[ tick ]
        us = self.upper_stress_bound[ tick ]

        if ls > us:
            raise ValueError("Lower stress exceeds upper stress")

        return ls * (us/ls) ** self.stressor.of(
            tick, self.ticks
        )

    def __iter__(self):

        for tick, chord in self.chords.items():

            if not isinstance(chord, list):
                note = chord
                chord = [note]
            yield Chord(
                    tick, self.voice, self.stress_of_tick(tick), chord
                )

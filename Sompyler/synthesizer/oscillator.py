# -*- coding: utf-8 -*-

import numpy as np
import re
from collections import deque
from .modulation import Modulation
from .shape import Shape
from ..synthesizer import BYTES_PER_CHANNEL, SAMPLING_RATE, normalize_amplitude

class Oscillator:

    def __init__( self, **args):

        self.osc_func = args.get('osc_func', _sine_wave)

        for attr in 'amplitude_modulation', 'frequency_modulation':
            if args.get(attr):
                mod = (args[attr] if isinstance(args[attr], Modulation)
                       else Modulation.from_string( args[attr] , args['pp_registry'],
                           self.osc_func
                       )
                     )
            else: mod = None
            setattr(self, attr, mod)

        ws = args.get('wave_shape')
        if ws:
            if not isinstance(ws, Shape):
                ws = Shape.from_string( ws )
            self.wave_shape = ws
            waveshape_res = 2 ** (BYTES_PER_CHANNEL * 8)
            waveshape_list = ws.render(waveshape_res)
            amplitudes = np.array(waveshape_list) - 1
            self.wave_shaper = lambda w: amplitudes[
                ( (w+1) / 2 * (waveshape_res-1) ).astype(np.int)
            ]
        else:
            self.wave_shape  = None
            self.wave_shaper = None

    def __call__(
        self, freq, iseq, phase=0, shaped_fm=None
    ):

        if isinstance(iseq, int):
            iseq = np.arange(iseq)
        else: assert isinstance(iseq, np.ndarray)

        if self.frequency_modulation:
            iseq = np.cumsum(
                self.frequency_modulation.modulate(iseq, freq)
            )
            if shaped_fm: iseq *= shaped_fm
        elif shaped_fm:
            iseq = np.cumsum( shaped_fm )

        wave = self.osc_func( iseq, freq, phase )

        if self.wave_shaper: wave = self.wave_shaper(wave)

        if self.amplitude_modulation:
            wave *= self.amplitude_modulation.modulate(iseq, freq)

        return wave

    def derive (self, **args):

        for i in (
                'osc_func', 'amplitude_modulation',
                'frequency_modulation', 'wave_shape'):
            if args.get(i): continue
            mine = getattr(self, i)
            if mine:
                args[i] = mine

        return self.__class__( **args )

    @classmethod
    def weighted_average( cls, left, dist, right ):

        args = {}

        for each in 'amplitude_modulation', 'frequency_modulation':
            l = getattr(left, each)
            r = getattr(right, each)
            if not ( l or r ):
                continue
            elif not l or l is r:
                args[each] = r
            elif not r:
                args[each] = l
            else:
                args[each] = l.weighted_average( l, dist, r )

        l = getattr(left, 'wave_shape')
        r = getattr(right, 'wave_shape')
        if l and r:
            args['wave_shape'] = l if l is r else l.weighted_average( l, dist, r)
        elif l or r:
            s = Shape("1:0;1,1")
            args['wave_shape'] = Shape.weighted_average( l or s, dist, r or s )

        if left.osc_func is right.osc_func:
            args['osc_func'] = left.osc_func
        else:
            args['osc_func'] = lambda l, f, p: (
                (1 - dist) * left.osc_func(l,f,p) + dist * right.osc_func(l,f,p)
            )

        return cls(**args)


def CORE_PRIMITIVE_OSCILLATORS (**osc_args):

    core_oscs = {
        'sine': _sine_wave,
        'sawtooth': _sawtooth_wave,
        'square': _square_wave,
        'triangle': _triangle_wave,
        'noise': _noise_generator,
    }

    if 'pp_registry' not in osc_args:
        osc_args['pp_registry'] = {}

    for (name, func) in core_oscs.items():
        osc_args[ 'osc_func' ] = func
        core_oscs[name] = Oscillator( **osc_args )

    return core_oscs


def _sine_wave(iseq, freq, phase):
    return np.sin(
        2*np.pi * iseq * freq / SAMPLING_RATE + phase
    )
def _sawtooth_wave(iseq, freq, phase):
    x = iseq * freq / SAMPLING_RATE + phase
    return 2 * (x - np.floor(x)) - 1

def _square_wave(iseq, freq, phase):
    x = iseq * freq / SAMPLING_RATE + phase
    return 2 * (np.floor(x) - np.round(x)) + 1

def _triangle_wave(iseq, freq, phase):
    x = iseq * freq / SAMPLING_RATE + phase
    return np.abs( x % 1 - 1/2) - 1/4

_RANDOMS_1SEC = np.random.random_sample(SAMPLING_RATE)

def _noise_generator(
    iseq, freq, phase=None,
    # rebalance_weight=1, sample_weight=1, last_sample_weight=1
    ):
    """ This noise generator is dynamic in that it respects the
        frequency. The phase is ignored.
    """
    raw_random_iter = np.nditer(_RANDOMS_1SEC)

    def getfreq_rnd():
        seq_iter = np.nditer(iseq)
        count = -1
        for i in seq_iter:
            try:
                rnd = next(raw_random_iter)
            except StopIteration:
                raw_random_iter.reset()
                rnd = next(raw_random_iter)
            yield ((i - count) * freq, rnd)
            count = i

    def rnd_samples():

        last_sample = 0

        count = 0

        posw = 1; negw = 1; recent_samples = deque()

        for (freq, sample) in getfreq_rnd():
        
            window_size = -2 * freq / SAMPLING_RATE + 1

            if window_size > 1:
                window_size = 1.0
                inv = False
            elif window_size < 0:
                window_size *= -1
                inv = True
            else:
                inv = False

            half_period_length = SAMPLING_RATE / (2*freq)

            earlier_sample = 0

            while len(recent_samples) > half_period_length:
                earlier_sample = recent_samples.popleft()
                if earlier_sample > 0:
                    posw -= earlier_sample
                else:
                    negw += earlier_sample

            if earlier_sample:
                tendency = posw / (posw + negw)
            else:
                tendency = (last_sample or sample) > 0

            window_size = 2 * (1 - window_size)
            lower_bound = last_sample - window_size * tendency
            upper_bound = lower_bound + window_size
        
            if lower_bound < -1:
                upper_bound -= lower_bound + 1
                lower_bound = -1
            elif upper_bound > 1:
                lower_bound -= upper_bound - 1
                upper_bound = 1
        
            if inv:
                lower_bound, upper_bound = (upper_bound * -1.0, lower_bound * -1.0)

            next_sample = lower_bound + sample % window_size
            
            count += 1;

            yield next_sample

            recent_samples.append(next_sample)
            if next_sample > 0:
                posw += next_sample
            else:
                negw -= next_sample

            last_sample = next_sample

    noise = np.fromiter(rnd_samples(), np.float32, iseq.size)
    normalize_amplitude(noise)
    return noise

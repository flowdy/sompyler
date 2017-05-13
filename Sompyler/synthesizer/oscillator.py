# -*- coding: utf-8 -*-

from __future__ import division
import numpy as np
from Sompyler.synthesizer import BYTES_PER_CHANNEL
from Sompyler.synthesizer.modulation import Modulation
from Sompyler.synthesizer.shape import Shape

class Oscillator:

    def __init__( self, **args):

        for attr in 'amplitude_modulation', 'frequency_modulation':
            if args.get(attr):
                mod = Modulation.from_string( args[attr], args['oscache'] )
            else: mod = None
            setattr(self, attr, mod)

        ws = args.get('wave_shape')
        if ws:
            if not isinstance(ws, Shape):
                ws = Shape.from_string( ws )
            self.wave_shape = ws
            waveshape_res = 2 ** (BYTES_PER_CHANNEL * 8 - 1)
            amplitudes = ws.render(waveshape_res)
            amplitudes = np.array( amplitudes + [
               -x for x in reversed(amplitudes[1:])
            ])
            self.wave_shaper = lambda w: amplitudes[
                (w * (waveshape_res-1) ).astype(np.int)
            ]
        else:
            self.wave_shape  = None
            self.wave_shaper = None

    def __call__(
        self, freq, iseq, phase=0, shaped_fm=None
    ):

        assert freq < 1 # freq must be passed as quotient: ?Hz/fps

        if isinstance(iseq, int):
            iseq = np.arange(iseq)
        else: assert isinstance(iseq, np.array)

        if self.frequency_modulation:
            iseq = np.cumsum(self.frequency_modulation.modulate(iseq, freq))
            if shaped_fm: iseq *= shaped_fm
        elif shaped_fm:
            iseq = np.cumsum( shaped_fm )

        wave = np.sin( 2*np.pi * iseq * freq + phase )

        if self.wave_shaper: wave = self.wave_shaper(wave)

        if self.amplitude_modulation:
            wave *= self.amplitude_modulation.modulate(iseq, freq)

        return wave

    def derive (self, **args):

        for i in 'amplitude_modulation', 'frequency_modulation', 'wave_shape':
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
            elif not l:
                args[each] = r
            elif not r:
                args[each] = l
            else:
                args[each] = getattr(left, each).weighted_average( l, dist, r )

        l = getattr(left, 'wave_shape')
        r = getattr(right, 'wave_shape')
        if l and r:
            args['wave_shape'] = l.weighted_average( l, dist, r)
        elif l or r:
            s = Shape("1:0;1,1")
            args['wave_shape'] = Shape.weighted_average( l or s, dist, r or s )

        return cls(**args)
    

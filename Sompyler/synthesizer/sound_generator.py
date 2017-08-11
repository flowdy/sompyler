# -*- coding: utf-8 -*-
from __future__ import division
from Sompyler.synthesizer.sympartial import Sympartial, Oscillator, log_to_linear
from Sompyler.synthesizer.envelope import Envelope, Shape
from Sompyler.synthesizer import CENT_PER_OCTAVE
from itertools import izip
from copy import copy
import numpy as np
import re

class SoundGenerator(Shape):
    __slots__ = ['heard_to_base_freq_divisor']
    def __init__(self, initial, the_list, term, heard_to_base_freq_divisor=1):
    
        tmp = []
    
        if initial is None:
            initial = next(p[2] for p in the_list if p[2] is not None)
        mylist = [(0.0, 0, initial)]
        mylist.extend(p for p in the_list)
    
        if term is None:
            term = next(p[2] for p in reversed(the_list) if p[2] is not None)
    
        mylist.append(( int(mylist[-1][0])+1.0, 0, term ))
    
        last_freq = 0
        last_symp = None
    
        for i1, v in enumerate(mylist):
    
            if len(v) == 2:
                freq0, volume = v
                symp = None
            else:
                freq0, volume, symp = v

            if symp is None:
                tmp.append(i1)
                continue

            for tv in tmp:
                freq = mylist[tv][0]
                volume = mylist[tv][1]
                left = freq - last_freq
                right = freq0 - freq
                dist = left / (left + right)
                mylist[tv] = (
                    freq, volume,
                    Sympartial.weighted_average(last_symp, dist, symp)
                )
    
            tmp = []
            last_freq = freq0
            last_symp = symp
    
        super(SoundGenerator, self).__init__((mylist[-2][0], 0), *mylist[1:-1])

        # TODO: more research and experimenting on that one. It is questionable that we can
        # calculate that so everyone hears the same pitch. For the time being, you can set
        # it manually if you want.
        # Numb weighted average makes tones too low to my ears:
        #   _heard_to_base_freq_divisor(coords)
        self.heard_to_base_freq_divisor = heard_to_base_freq_divisor 

    def render(self, heard_freq, duration=0, args=None):

        base_freq = heard_freq / self.heard_to_base_freq_divisor

        if args is None: args = {}
        elif not isinstance(args, dict):
             raise Exception(
                 "further arg(s) have wrong type: {}".format(
                 type(args)
             ))
        samples = np.array([0.0])
        sympit = self.iterate_coords(1)
        total_share = 0

        for s in sympit:
            sympres = s.symp.render(
                base_freq * s.x, s.y, duration, args
            )
            len1 = len(samples)
            len2 = len(sympres)
            if len1 > len2:
                sympres = np.append( sympres, np.zeros(len1-len2) )
            elif len2 > len1:
                samples = np.append( samples, np.zeros(len2-len1) )
            samples = samples + sympres
            
        return samples

def _heard_to_base_freq_divisor (freq_factors):
    total = 0
    weights = 0
    for c in freq_factors.iterate_coords():
        sp = log_to_linear( c.y )
        total += c.x * sp
        weights += sp

    return total / weights


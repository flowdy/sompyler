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
    def __new__(cls, initial, the_list, term):
    
        tmp = []
    
        if initial is None:
            initial = next(p[2] for p in the_list if p[2] is not None)
        mylist = [(0.0, 0, initial)]
        mylist.extend(p for p in the_list)
    
        if term is None:
            term = next(p[2] for p in reversed(the_list) if p[2] is not None)
    
        mylist.append(( int(mylist[-1])+1.0, 0, term ))
    
        last_freq = None
        last_symp = None
    
        for i1, v in enumerate(mylist):
    
            if v is None:
                tmp.append(i1)
                continue

            freq0, volume, symp = parse_sympartial(v)
            coords.append( (freq0, volume, symp) )
    
            for tv in tmp:
                freq, volume, _ = mylist[tv]
                left = freq - last_freq
                right = freq0 - freq
                dist = left / (left + right)
                mylist[tv] = (
                    freq, volume,
                    Envelope.weighted_average(last_env, dist, env)
                )
    
            tmp = []
            last_freq = freq
            last_symp = symp
    
        self = super(SoundGenerator, cls).__new__(cls, *coords)
        self.heard_to_base_freq_divisor = _heard_to_base_freq_divisor(coords)
        self.sympartial_registry = copy(sympartial_registry) if sympartial_registry else {}

    def render(self, heard_freq, duration, args=None):

        base_freq = heard_freq / self.heard_to_base_freq_divisor

        if args is None: args = {}
        elif not isinstance(args, dict):
             raise Exception(
                 "further arg(s) have wrong type: {}".format(
                 type(args)
             ))
        samples = np.array([0.0])
        sympit = self.iterate_coords()
        total_share = 0

        for s in sympit:
            sympres = s['symp'].render(
                base_freq * s['freq_factor'], s['volume'], duration, args
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


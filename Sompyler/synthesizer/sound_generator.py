# -*- coding: utf-8 -*-

from __future__ import division
from Sompyler.synthesizer.sympartial import Sympartial, Oscillator, log_to_linear
from Sompyler.synthesizer.envelope import Envelope, Shape
from Sompyler.synthesizer import CENT_PER_OCTAVE
from itertools import izip
import numpy as np
import re

#import matplotlib.pyplot as plt

class SoundGenerator(object):

    def __init__ (self, freq_factors, sympartials, oscache):
        self.freq_factors = freq_factors
        self.sympartials = sympartials
        self.named_oscillators = oscache
        self.heard_to_base_freq_divisor = _heard_to_base_freq_divisor(
             freq_factors
        )

    @classmethod
    def from_partial_spec_list (cls, partials, base=None):

        freq_factors = [ None ]

        if base:
            oscache, initial_symp, final_ff, final_symp = base.derive()
            sympartials = [first_symp]
        else:
            oscache = {}
            final_ff = None
            final_symp = None
            sympartials = [None]

        last_ff = 0

        for p in cls.parse_sympartials( partials, oscache ):
            factor, deviation, share, symp = p
            freq_factor = factor * 2 ** ( deviation / CENT_PER_OCTAVE )
            if not freq_factor > last_ff:
                raise Exception(
                    "Frequence factors do not increase continuously"
                )
            last_ff = freq_factor
            freq_factors.append( (freq_factor, share) )
            sympartials.append(symp)

        freq_factors[0] = (freq_factor, 0)

        SoundGenerator._interpolate_gaps( sympartials, final_ff, final_symp )
 
        return cls( Shape(*freq_factors), sympartials, oscache )

    @staticmethod
    def _interpolate_gaps( sympartials, final_ff, final_symp ):

        lasti = 0
        for (c, s) in enumerate(sympartials[1:]):

            if s.envelope:
                last = c
                nexti = 0

            else:
                fdist = freq_factors[c].x - freq_factors[lasti].y
                if not nexti:
                    nexti = next(
                        c+i+1 for (i, s) in enumerate( sympartials[c+1:] )
                            if s.envelope
                    )
                fdist /= 1.0 * (
                    ( freq_factors[nexti].x if nexti else final_ff )
                    - freq_factors[lasti].x
                )
                sympartials[c] = Sympartial.weighted_average(
                    sympartials[lasti], fdist,
                    sympartials[nexti][1] if nexti else final_symp
                )
                
    def render(self, heard_freq, duration, args=None):

        base_freq = heard_freq / self.heard_to_base_freq_divisor

        if args is None: args = {}
        elif not isinstance(args, dict):
             raise Exception(
                 "further arg(s) have wrong type: {}".format(
                 type(args)
             ))
        samples = np.array([0.0])
        sympit = self.iterate_chain()
        total_share = 0

        for (f, share, symp) in sympit:
            sympres = symp.render(base_freq * f, share, duration, args)
            len1 = len(samples)
            len2 = len(sympres)
            if len1 > len2:
                sympres = np.append( sympres, np.zeros(len1-len2) )
            elif len2 > len1:
                samples = np.append( samples, np.zeros(len2-len1) )
            samples = samples + sympres
            
        return samples

    def iterate_chain(self):
        sympit = iter(self.sympartials)
        next(sympit) # skip None
        ff = self.freq_factors.iterate_coords(1)
        for (p, symp) in izip(ff, sympit):
            yield (p.x, p.y, symp)

    def derive(self):
        osc = {}
        osc.update(self.named_oscillators)
        return (
            osc, self.sympartials[1],
            self.frequence_factors[-1],
            self.sympartials[-1]
        )

    @classmethod
    def weighted_average (cls, left, dist, right):

        lff = left.freq_factors
        rff = right.freq_factors
        loc = left.oscillators[1:]
        roc = right.oscillators[1:]

        bff = Shape.weighted_average( lff, dist, rff )
        boc = [None]

        for i, lo in enumerate(loc):
            ro = roc[i]
            if not (lo or ro):
                boc.append(None)
                continue
            boc.append( Oscillator.weighted_average(
                lo, dist, ro
            ))

        return cls(bff, boc)

    @staticmethod
    def parse_sympartials (specs, oscache):
        """
        returns a tuple of two items
            1. either name of an oscillator to reuse in modulations,
               or a subtuple: (freq_factor, deviation, volume, sympartial)
            2. oscillator object
        """

        for string in specs:
            head, attrs = string.split(" ", 1)
    
            attr_dir = dict(
                (key, None) for key in ["A", "S", "R", "O", "AM", "FM", "WS"]
            )
            for attr in attrs.split(" "):
                m = re.match(r"([A-Z]+)\(([^)]+)\)", attr)
                if not m: raise Exception(
                    "Cannot parse partial attribute: {}".format(attr)
                )

                key, value = m.groups()
                if not key in attr_dir:
                    raise Exception(
                        "Attribute {} is not supported".format(key)
                    )
                attr_dir[ key ] = value
    
            osc_args = {
                'amplitude_modulation': attr_dir.pop('AM', None),
                'frequency_modulation': attr_dir.pop('FM', None),
                'wave_shape': attr_dir.pop("WS", None),
                'oscache': oscache
            }

            oscillator = attr_dir.pop("O", None)
            if oscillator:
               oscillator = _oscache[ oscillator ].derive(**osc_args)
            else:
               oscillator = Oscillator(**osc_args)

            if head.startswith('$'):

                _oscache[ head[1:] ] = oscillator
                continue

            else:

                m = re.match(r"(/?\d+)([+-]\d+)?@(\d+)$", head)
                if not m: raise Exception(
                    "Syntax error in sympartial definition. Got {}. Expecting {}".format(
                        head,
                        """
                        'N?deltacent@volume', i.e.
                         N: Integer frequence factor;
                          ?deltacent: +n or -n cent deviation, signed
                                     volume: 0 to 100 dB i.e. % of assumed total accoustic pressure 100dB
                        """
                    )
                )

                nfactor = m.group(1)
                # nfactor may be undertone: "/n" -> 1/n
                if nfactor.startswith('/'):
                    nfactor = 1 / int(nfactor[1:])
                else:
                    nfactor = int(nfactor)

                deviation = int(m.group(2) or 0)
                share = int(m.group(3)) / 100

                yield (nfactor, deviation, share, Sympartial(
                    Envelope(
                        attack=attr_dir.pop("A", None),
                        sustain=attr_dir.pop("S", None),
                        release=attr_dir.pop("R", None)
                    ) if attr_dir else None, oscillator
                ))

def _heard_to_base_freq_divisor (freq_factors):
    total = 0
    weights = 0
    for c in freq_factors.iterate_coords():
        sp = log_to_linear( c.y )
        total += c.x * sp
        weights += sp

    return total / weights

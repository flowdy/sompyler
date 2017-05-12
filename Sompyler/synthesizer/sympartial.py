# -*- coding: utf-8 -*-

from __future__ import division
from Sompyler.synthesizer import SAMPLING_RATE
from Sompyler.synthesizer.oscillator import Oscillator, Shape
import numpy as np
import re
import copy

class Sympartial(object):
    """
    A Sympartial is a partial that may be accompanied by dependent partials
    implied by modulation of its amplitude, frequency, and/or by wave shaping.
    Main and dependent partials are all shaped with a common envelope.
    """

    def __init__(
        self, envelope=None, oscillator=None
    ):
        self.envelope = envelope
        self.oscillator = oscillator

    def render(self, freq, share, duration, args):

        if share:
            envelope = self.envelope
            if envelope is None:
                iseq = np.arange(duration * SAMPLING_RATE)
            else:
                envelope = self.envelope
                share *= np.array(envelope.render(duration))
                iseq = np.arange(share.size)
        else:
            return np.zeros(duration * SAMPLING_RATE)

        if 'shaped_fm' in args and not isinstance(args['shaped_fm'], Shape):
            args['shaped_fm'] = Shape.from_string(
                "1:" + args['shaped_fm']
            ).render(iseq.size)

        osc_args = copy.copy(args)

        # resolve dB -> linear amplitude size
        share = log_to_linear(share)

        shaped_am = osc_args.pop('shaped_am', None)
        if shaped_am:
            shaped_am = Shape.from_string(shaped_am)
            share *= np.array( shaped_am.render(iseq.size) )

        return share * self.oscillator(
            freq / SAMPLING_RATE, iseq, 0, **osc_args
        )

    @classmethod
    def weighted_average(cls, left, dist, other):

        for each in ('envelope', 'oscillator'):
            l = getattr(left, each)
            r = getattr(right, each)
            if not (l and r):
                continue
            if not l:
                args[each] = r
            elif not r:
                args[each] = l
            args[each] = l.weighted_average( l, dist, r )

        return cls(**args)

def log_to_linear(num):
    return np.power( 10.0, -5 * ( 1 - num ) )

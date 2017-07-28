# -*- coding: utf-8 -*-

from __future__ import division
from Sompyler.synthesizer import SAMPLING_RATE
from Sompyler.synthesizer.oscillator import Oscillator
from Sompyler.synthesizer.envelope import Envelope, Shape
import numpy as np
import re
import copy

ABBREV_ARGS = {
    'A': 'attack',
    'S': "sustain",
    'B': "boost",
    'R': "release",
    'AM': "amplitude_modulation",
    'FM': "frequency_modulation",
    'WS': "wave_shape",
}

ENV_ARGS = ('A', 'S', 'B', 'R')
OSC_ARGS = ('AM', 'FM', 'WS')

def _gather_args (args):

    env_args = {}; osc_args = {}

    for i in ENV_ARGS:
         val = args.get(i)
         if val: env_args[ ABBREV_ARGS[i] ] = val

    for i in OSC_ARGS:
         val = args.get(i)
         if val: osc_args[ ABBREV_ARGS[i] ] = val

    return (env_args, osc_args)

class Sympartial(object):
    """
    A Sympartial is a partial that may be accompanied by dependent partials
    implied by modulation of its amplitude, frequency, and/or by wave shaping.
    Main and dependent partials are all shaped with the same envelope.
    """

    def __init__( self, envelope, oscillator ):
        self.envelope = envelope
        self.oscillator = oscillator

    @classmethod
    def from_props ( cls, symp_registry={}, **args ):
        envelope_args, oscillator_args = _gather_args(args)

        osc_args['symp_registry'] = symp_registry
        osc = args['O']
        if osc:
            oscillator = symp_registry[osc].oscillator
            oscillator = (
                oscillator.derive(**oscillator_args)
                    if oscillator_args else oscillator
            )
        else:
            oscillator = Oscillator(**oscillator_args)

        return cls( Envelope(**envelope_args), 
                    oscillator
               )

    def render(self, freq, share, duration, args):

        envelope = None
        if share:
            envelope = self.envelope
            if envelope is None:
                iseq = np.arange(duration * SAMPLING_RATE)
                envelope = 1 # constant
            else:
                envelope = np.array(envelope.render(duration))
                share *= envelope
                iseq = np.arange(envelope.size)
        else:
            return np.zeros(duration * SAMPLING_RATE)

        if 'shaped_fm' in args and not isinstance(args['shaped_fm'], np.array):
            args['shaped_fm'] = Shape.from_string(
                "1:" + args['shaped_fm']
            ).render(iseq.size)

        osc_args = copy.copy(args)

        # resolve dB -> linear amplitude size
        share = log_to_linear(share)

        shaped_am = osc_args.pop('shaped_am', None)
        if shaped_am:
            if not instance(shaped_am, Shape):
                shaped_am = Shape.from_string(shaped_am)
            share *= np.array( shaped_am.render(iseq.size) )

        return share * self.oscillator(
            freq / SAMPLING_RATE, iseq, 0, **osc_args
        )

    def derive(self, symp_registry={}, **args):

        env_args, osc_args = _gather_args(args)
        osc_args['symp_registry'] = symp_registry

        if env_args:
            envelope = self.envelope.derive(**env_args)
        else:
            envelope = self.envelope

        if osc_args:
            oscillator = self.oscillator.derive(**osc_args)
        else:
            oscillator = self.oscillator

        return self.__class__(envelope, oscillator)

    @classmethod
    def weighted_average(cls, left, dist, other):

        for each in ('envelope', 'oscillator'):
            l = getattr(left, each)
            r = getattr(right, each)
            if l is r:
                args[each] = l
            else:
                args[each] = l.weighted_average( l, dist, r )

        return cls(**args)

def log_to_linear(num):
    return np.power( 10.0, -5 * ( 1 - num ) )

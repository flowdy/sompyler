# -*- coding: utf-8 -*-

from __future__ import division
from Sompyler.synthesizer import SAMPLING_RATE
from Sompyler.synthesizer.shape import Shape
from numpy import pi, sin
import re

class Modulation(object):

    def __init__(
        self, frequency, mod_share, base_share,
        phase_angle_degrees=0, overdrive=True, arg1_periods_unit=False, 
        use_oscillator=None, envelope=None
    ):
        """ We have a constant socket and a part to modulate, the heights
            of which are given in a relation (base_share:mod_share)

        [-------|-------|-------|-------] Frequency in intervals per second
           *     *     *     *     *    T
          ***   ***   ***   ***   ***   | ^ mod_share (3)
         ***** ***** ***** ***** *****  | = Modulation intensity in relation
        ******************************* –   to ...
        ******************************* |
        ******************************* |
        ******************************* |
        ******************************* | ^ base_share (6)
        ******************************* _ = Minimum amplitude or frequency
        """
        self.frequency  = frequency
        self.mod_share  = mod_share
        self.base_share = base_share 
        self.is_dynamic = arg1_periods_unit
        self.init_phase = phase_angle_degrees * pi / 180
        self.overdrive = overdrive # center base line

        func = use_oscillator
        if not func:
           func = (lambda f, l, s: sin(2*pi * f * l + s))
        if envelope:
           inner_func = func
           func = lambda f, l, s: envelope.render(l.size) * inner_func(f, l, s)

        self.function = func

    @classmethod
    def from_string(cls, string, oscache):
        m = re.match(
            r"(\d+)(p)?(?:\*(\w+))?;(\d+):(\d+)(?:;([+-]\d+))?(?:,env:(.+))?",
            string
        )

        if m:

            opts = {}
            ml = [
                int(m.group(1)),
                int(m.group(4)) if m.group(4) else None,
                int(m.group(5)) if m.group(5) else None,
                int(m.group(6)) if m.group(6) else 0
            ]

            opts['arg1_periods_unit'] = bool(m.group(2))

            if m.group(3):
                o = oscache[ m.group(3) ]
                if o:
                    opts['use_oscillator'] = o
                else: raise Exception(
                    "Oscillator not defined: {}".format(m.group(3))
                )

            if m.group(7):
                opts['envelope'] = Shape.from_string( "1:" + m.group(7) )

            return Modulation(*ml, **opts)

        else:
            raise Exception("Modulation definition syntax")

    def modulate(self, iseq, freq=None):
        b = self.base_share
        m = self.mod_share
        f = ( freq * self.frequency if self.is_dynamic
              else self.frequency / SAMPLING_RATE
            )
        p = self.init_phase
        o = (m + b) / (2*b) + 0.5 if self.overdrive else 1
        return o * (
            m * (self.function(f, iseq, p) + 1) / 2 + b
        ) / (m + b)

    @classmethod
    def weighted_average(cls, left, dist, right):

        assert not ( dist < 0 or dist > 1 )

        avg = lambda a, b: (1 - dist) * a + dist * b

        attr = {}

        for p in ( 'mod_share', 'base_share' ):            
            lattr = getattr(left, p) / (left.mod_share + left.base_share)
            lattr = getattr(other, p) / (right.mod_share + right.base_share)
            attr[p] = avg(lattr, rattr)

        for p in ( 'frequency', 'factor', 'shift' ):

            lattr = getattr(left, p)
            rattr = getattr(right, p)

            if lattr and rattr:
                attr[p] = avg( lattr, rattr )
            elif lattr or rattr:
                attr[p] = lattr or rattr

        attr['overdrive'] = left.overdrive if dist < 0.5 else right.overdrive

        if isinstance(left.function, 'Oscillator') and \
           isinstance(right.function, 'Oscillator'):
            attr['function'] = Oscillator.weighted_average(
                left.function, dist, right.function
            )
        else:
            # We do not know how to mean unknown functions, so we decide
            # for the left when dist is below 0.5, for the right otherwise.
            attr['function'] = left.function if dist < 0.5 else right.function

        return Modulation(**attr)



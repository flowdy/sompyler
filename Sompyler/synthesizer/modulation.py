# -*- coding: utf-8 -*-

from __future__ import division
from .shape import Shape
from numpy import pi, sin
import re

class Modulation:

    def __init__(
        self, frequency, mod_share, base_share, oscillator,
        phase_angle_degrees=0, overdrive=True, arg1_frequency_unit=False,
        envelope=None
    ):
        """ We have a constant socket and a part to modulate, the heights
            of which are given in a relation (mod_share:base_share)

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
        self.is_dynamic = arg1_frequency_unit
        self.init_phase = phase_angle_degrees / 360.0
        self.overdrive = overdrive # center base line
        self.envelope = envelope
        self.function = oscillator

    @classmethod
    def from_string(cls, string, cache):
        m = re.fullmatch(
                r"([\d.]+)(f)?(?:@(\w+))?(?:\[([^]]+)\])?;"
                r"(\d+):(\d+)([+-]\d+)?",
            string
        )

        if m:

            if m.group(4) is None:
                env = None
            else:
                env = Shape.from_string(m.group(4))

            return Modulation(
                   frequency=float(m.group(1)),
                   mod_share=int(m.group(5)) if m.group(5) else None,
                   base_share=int(m.group(6)) if m.group(6) else None,
                   phase_angle_degrees=int(m.group(7)) if m.group(7) else 0,
                   arg1_frequency_unit=bool(m.group(2)),
                   oscillator=cache(m.group(3) or 'sine').get('O'),
                   envelope=env
                )

        else:
            raise RuntimeError("Modulation definition syntax")

    def modulate(self, iseq, freq=None):
        b = self.base_share
        m = self.mod_share
        f = ( freq * self.frequency if self.is_dynamic
              else self.frequency
            )
        e = self.envelope.render(len(iseq)) if self.envelope else 1
        p = self.init_phase
        o = (
            (m + b) / (2*b) + 0.5 if self.overdrive else 1
            )
        return o * (
            m * (e * self.function(iseq, f, p) + 1) / 2 + b
        ) / (m + b)

    @classmethod
    def weighted_average(cls, left, dist, right):

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

        if left.function is right.function:
            attr['function'] = left.function
        elif isinstance(left.function, 'Oscillator') and \
             isinstance(right.function, 'Oscillator'):
            attr['function'] = Oscillator.weighted_average(
                                   left.function, dist, right.function
                               )
        else:
            # We do not know how to mean unknown functions, so we apply both
            # and mean the result. Please use this sparely if at all, as it is
            # not performant.
            attr['function'] = lambda f, l, s: avg(
                left.function(f, l, s), right.function(f, l, s)
            )
            
        return Modulation(**attr)



# -*- coding: utf8 -*-

import numpy as np

class Modulation:

    def __init__(
        self, frequency, base_share, mod_share,
        shift=0, overdrive=True, factor=None
    ):
        self.base_share = base_share 
        self.mod_share  = mod_share
        if frequency:
            self.frequency = frequency * (factor or 1)
        elif factor:
            self.factor = factor
        else:
            raise Exception("No factor passed to use for base frequency")
        self.shift     = shift
        self.overdrive = overdrive

    def modulate(self, iseq, freq=None):
        """ Caution: Not quite sure if that really does what it is supposed to.
              It is just a very naive way to make a tone more dynamic, spawned
              from my rough intuition.
               
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
        b = self.base_share
        m = self.mod_share
        f = (self.frequency or self.factor * freq)
        s = self.shift
        o = (m + b) / (2*b) + 0.5 if self.overdrive else 1
        return o * (
            m * (np.sin(2*np.pi * iseq * f/fs + s) + 1) / 2 + b
        ) / (m + b)



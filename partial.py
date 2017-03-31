# -*- coding: utf8 -*-

import numpy as np

class Partial:
    def __init__(self, nfactor, share, shape=None, deviation=0, am=None, fm=None):
        self.nfactor = nfactor
        self.deviation = deviation
        self.share = share
        self.shape = shape
        self.amplitude_modulation = am
        self.frequency_modulation = fm

    def render_samples(self, freq, iseq, shaped_fm=None):
        n = self.nfactor
        d = self.deviation
        s = self.share

        if self.amplitude_modulation is not None:
            s *= self.amplitude_modulation.modulate(iseq, freq)

        if self.shape is not None:
            s *= np.array(self.shape.render(iseq.size))

        if self.frequency_modulation is not None:
            iseq = np.cumsum(self.frequency_modulation.modulate(iseq, freq))
            if shaped_fm: iseq *= shaped_fm
        elif shaped_fm:
            iseq = np.cumsum( shaped_fm )
 
        return np.sin(
            2*np.pi * iseq * (n*freq+d) / fs
        ) * np.power(10.0, -5 * ( 1 - s ))



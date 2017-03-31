# -*- coding: utf-8 -*-

import numpy as np

class Instrument:

    def __init__(self, character):
        self.timbre = character['default']

    def get_samples (self, freq, duration):
        duration = 240 / bpm * duration
        partial_samples = []
        divisor = 0
        iseq = np.arange(fs*duration) # integer sequence 1 .. fs*duration
        if not freq: return 0*iseq
        for partial_tone in self.timbre:
            partial_samples.append(partial_tone.render_samples(freq, iseq))
            divisor += partial_tone.share
    
        # mix partials by their weights and return an numpy array ready to
        # play
        return (sum(partial_samples)/divisor).astype(np.float32)



# -*- coding: utf-8 -*-

import numpy as np
import Partial from partial
import codecs
import yaml
import re
from partial import Partial
from modulation import Modulation

class Instrument:

    fs = 44100

    def __init__(self, character):
        self.timbre = character['default']

    def get_samples (self, freq, duration):
        duration = fs * 240 / bpm * duration
        partial_samples = []
        if not freq: return 
        for partial_tone in self.timbre:
            partial_samples.append(partial_tone.render_samples(freq, duration))
    
        # mix partials (to be scaled later based on maximum)
        return sum(partial_samples) # .astype(np.float32) done by channel

    def from(file):
        with codecs.open(file, encoding="utf-8") as splidef:
             spli = yaml.safe_load(splidef)
        if "sompyler-instrument" in spli['MIME']:
        partials = spli["character"]["default"]
        for i, p in enumerate(partials):
            partials[i] = parse_partial(p)

    def parse_partial (string):
        nfactor, deltacent, dB, attrs = string.split(" ", 3)
    
        share = int(dB) / 100.0
    
        # nfactor may be undertone: "/n" -> 1/n
        if nfactor.startswith('/'):
            nfactor = 1 / int(nfactor[1:])
        else:
            nfactor = int(nfactor)
    
        attr_dir = {}
        for attr in attrs.split(" "):
            m = re.match(r"([A-Z]+)\(([^)]+)\)", attr)
            if not m: raise Exception("Cannot parse partial attribute " + m)
            attr_dir[ m.group(1) ] = m.group(2)
    
        shapes = None
        if attr_dir['S']:
            shapes = []
            for bezier in attr_dir['S'].split("|",3):
                if not bezier:
                    shapes.append(0)
                    continue
                coords, bezier = bezier.split(":",2)
                coords = [[ int(coords or 0), 0 ]] # list with 1 item
                m = re.match("^(\d+);", bezier)
                coords[0][1] = int(m.group(1)) if m else 0
                if m:
                    __, bezier = bezier.split(";",1)
                for m in bezier.split(";"):
                    coords.append([ int(n) for n in m.split(",") ])
                shapes.append(coords)
    
        for i in 'AM', 'FM':
            if attr_dir[i]:
                m = re.match(r"(\d+)(f?),(\d+),(\d+)", del attr_dir[i])
                ml = [
                    int(m.group(1)), int(m.group(3)), int(m.group(4))
                ] if m else None
                if m:
                    if m.group(2):
                        opts['factor'] = ml[1]
                        ml[1] = None
                    attr_dir[ i.lowercase() ] = Modulation(*ml, **opts)
    
        return Partial( nfactor, share, shapes, deltacent, **attr_dir )



# -*- coding: utf-8 -*-
from __future__ import division
import pyaudio
import numpy as np
import time
import atexit
import sys
import codecs
from instrument import Instrument
from shape import Shape
from modulation import Modulation
from partial import Partial
from itertools import imap
from sine2wav import main as write_wavefile

fs = 44100       # sampling rate, Hz, must be integer
bpm = 120

tones = {}
with codecs.open("tones.txt", encoding="utf-8") as t:
    for line in t:
        if line.startswith("#"):
            continue
        (key, val) = line.rstrip().split()
        tones[key] = float(val)

def main():
    
    #play_melody(1, "simple", [440, 3])
    time.sleep(1)
    #play_melody(1, 'vibr', [220.0, 5]) # a minute of sound with vibrato
    #play_melody(1, 'many', [440.0, 60])
    play_melody( 1, 'string', ['', 1/2],
        ['C4', 1/8], ['D4', 1/8], ['E4', 1/8], ['F4', 1/8], ['G4', 1/4], ['G4', 1/4],
        ['A4', 1/8], ['A4', 1/8], ['A4', 1/8], ['A4', 1/8], ['G4', 1/2], ['A4', 1/8], ['A4', 1/8], ['A4', 1/8], ['A4', 1/8], ['G4', 1/2],
        ['F4', 1/8], ['F4', 1/8], ['F4', 1/8], ['F4', 1/8], ['E4', 1/4], ['E4', 1/4], ['G4', 1/8], ['G4', 1/8], ['G4', 1/8], ['G4', 1/8],
        ['C4', 1/2]
    )
    

## TODO: In eigene Dateien auslagern
# generate samples, note conversion to float32 array
P = Partial
M = Modulation

timbre_inventory = {
    'simple': [P(1)],
    'test': [P(1), P(2,0.13), P(3,0.05)],
    'many': [P(1,15), P(2,0.5), P(3,0.05), P(4,0.3),P(5,0.1),P(6,0.07), P(7,0.33),P(8,0.1),P(9,0.03),P(10,0.01)],
    'vibr': [P(1), P(2,0.03), P(3,0.15,fm=M(6,8,3))],
    'string': [
      # TODO: In Dezibel umrechnen!!
        P(1), P(2,0.5), P(3,0.15), P(4,0.03), P(5,0.03), P(6,0.1),
        P(7,0.15), P(8,0.2), P(9,0.01), P(10,0.03), P(11,0.01), P(12,0.02),
        P(13,0.08), P(14,0.04), P(15,0.02), P(16,0.01)
    ],
} # ,fm=M(30,50,1,-45)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=fs,
                output=True)


def play_melody(volume, timbre, *sounds):
    print "Playing", sounds
    for sound in sounds:
        freq = tones.get(sound[0])
        if freq: sound[0] = freq
        stream(volume*get_samples(timbre, *sound))

def cleanup():
    p.terminate()
    print "PyAudio terminated."

if __name__ == "__main__":
   if len(sys.argv) > 1:
       melodies = []
       stream = lambda x: melodies.append(x) and x
       main()
       melodies = np.concatenate(melodies)
       channels = ((imap(float,np.nditer(melodies)),) for c in range(2)) 
       write_wavefile(channels)
   else:
       orig_stream = stream
       stream = stream.write
       main()
       orig_stream.stop_stream()
       orig_stream.close()

atexit.register(cleanup)

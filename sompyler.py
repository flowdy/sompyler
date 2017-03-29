# -*- coding: utf-8 -*-
import pyaudio
import numpy as np
import time
import atexit

fs = 44100       # sampling rate, Hz, must be integer

def main():
    
    play_melody(1, ["simple", 440, 3])
    time.sleep(1)
    play_melody(1, ['vibr',220.0, 10]) # a minute of sound with vibrato
    #play_melody(1, ['many',440.0, 60]) # a minute of sound with vibrato
    #play_melody(1, ['string', 294.0, 1])
    
    stream.stop_stream()

# generate samples, note conversion to float32 array
def get_samples (timbre, freq, duration):
     partial_samples = []
     divisor = 0
     iseq = np.arange(fs*duration) # integer sequence 1 .. fs*duration
     for partial_tone in timbre_inventory[timbre]:
         partial_samples.append(partial_tone.render_samples(freq, iseq))
         divisor += partial_tone.share

     # mix partials by their weights and return an numpy array ready to
     # play
     return (sum(partial_samples)/divisor).astype(np.float32)

class Modulation:

    def __init__(self, frequency, base_share, mod_share, overdrive=True):
        self.base_share = base_share 
        self.mod_share  = mod_share
        self.frequency = frequency
        self.overdrive = overdrive

    def modulate(self, iseq):
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
        f = self.frequency
        o = (m + b) / (2*b) + 0.5 if self.overdrive else 1
        return o * (
            m * (np.sin(2*np.pi * iseq * f/fs) + 1) / 2 + b
        ) / (m + b)

class Partial:
    def __init__(self, nfactor=1, share=1, deviation=0, am=None, fm=None):
        self.nfactor = nfactor
        self.deviation = deviation
        self.share = share
        self.amplitude_modulation = am
        self.frequency_modulation = fm

    def render_samples(self, freq, iseq):
        n = self.nfactor
        d = self.deviation
        s = self.share

        if self.amplitude_modulation is not None:
            s *= self.amplitude_modulation.modulate(iseq)
        if self.frequency_modulation is not None:
            iseq = np.cumsum(self.frequency_modulation.modulate(iseq))
 
        return np.sin( 2*np.pi * iseq * (n*freq+d) / fs ) * s

P = Partial
M = Modulation

timbre_inventory = {
    'simple': [P(1)],
    'test': [P(1), P(2,0.13), P(3,0.05)],
    'many': [P(1,15), P(2,0.5), P(3,0.05), P(4,0.3),P(5,0.1),P(6,0.07), P(7,0.33),P(8,0.1),P(9,0.03),P(10,0.01)],
    'vibr': [P(1), P(2,0.03), P(3,0.15,fm=M(6,8,3))],
    'string': [
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

def play_melody(volume, *sounds):
    for sound in sounds:
        stream.write(volume*get_samples(*sound))
    
def cleanup():
    stream.close()
    p.terminate()
    print "PyAudio terminated."

if __name__ == "__main__":
   main()

atexit.register(cleanup)


SAMPLING_RATE     = 44100
CENT_PER_OCTAVE   = 1200
BYTES_PER_CHANNEL = 2

def normalize_amplitude(sound, stress=None):
    dmin = sound.min()
    dmax = sound.max()
    sound -= dmin
    sound /= max(dmax, -dmin)
    sound -= 1
    if stress is not None:
        sound *= stress

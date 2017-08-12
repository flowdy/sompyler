
SAMPLING_RATE     = 22050
CENT_PER_OCTAVE   = 1200
BYTES_PER_CHANNEL = 2

def normalize_amplitude(sound):
    dmin = sound.min()
    dmax = sound.max()
    sound -= dmin
    sound /= max(dmax, -dmin)
    sound -= 1

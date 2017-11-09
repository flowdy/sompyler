
SAMPLING_RATE     = 44100
CENT_PER_OCTAVE   = 1200
BYTES_PER_CHANNEL = 2

def normalize_amplitude(sound, stress=1):
    sound /= max(sound.max(), -sound.min()) / stress
    return sound

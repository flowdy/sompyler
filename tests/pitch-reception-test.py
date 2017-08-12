from sine2wav import write_wavefile
from Sompyler.synthesizer import normalize_amplitude
# import matplotlib.pyplot as plt

from Sompyler.instrument import Variation

def write_file(sound, filename):
    print "Writing", filename
    normalize_amplitude(sound)
    channels = ((x for x in sound),)
    write_wavefile(filename, channels, len(sound), 1, 2, 22050)

write_file(
    Variation.from_definition({
        'A': "0.03:1,100",
        'R': "4.8:100;100,95;1000,0",
        'O': "sine",
        'PARTIALS': [ 100 ]
    }).sound_generator_for({}).render(440),
    "/tmp/4CaC.wav"
)

write_file(
    Variation.from_definition({
        'A': "0.03:1,100",
        'R': "4.8:100;100,95;1000,0",
        'O': "sine",
        'PARTIALS': [ 100, 75, 20, 15, 10 ]
    }).sound_generator_for({}).render(440),
    "/tmp/K7ay.wav"
)

write_file(
    Variation.from_definition({
        'A': "0.03:1,100",
        'R': "4.8:100;100,95;1000,0",
        'O': "sine",
        'PARTIALS': [ { -2786: 100 }, 75, 20, 15, 10 ]
    }).sound_generator_for({}).render(2200),
    "/tmp/PZJU.wav"
)

write_file(
    Variation.from_definition({
        'A': "0.03:1,100",
        'R': "4.8:100;100,95;1000,0",
        'O': "sine",
        'PARTIALS': [ { -2786: 100, 0: 100 }, 75, 20, 15, 10 ]
    }).sound_generator_for({}).render(2200),
    "/tmp/Zgb4.wav"
)

write_file(
    Variation.from_definition({
        'A': "0.03:1,100",
        'R': "4.8:100;100,95;1000,0",
        'O': "sine",
        'PARTIALS': [ 10, 15, 20, 75, 100 ]
    }).sound_generator_for({}).render(440),
    "/tmp/yr2S.wav"
)

write_file(
    Variation.from_definition({
        'A': "0.03:1,100",
        'R': "4.8:100;100,95;1000,0",
        'O': "sine",
        'PARTIALS': [ 0, 0, 0, 0, 100 ]
    }).sound_generator_for({}).render(440),
    "/tmp/g66X.wav"
)


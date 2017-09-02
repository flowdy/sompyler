import yaml, numpy
from sys import argv
from sine2wav import write_wavefile
from Sompyler.instrument import Variation
from Sompyler.synthesizer import normalize_amplitude

trumpet = yaml.load(open("instruments/dev-trumpet.spli", "r"))

trumpet = Variation.from_definition(trumpet['character'])

def forge_sound(pitch, length, stress, **note):

    sgnote = dict(note.items())
    sgnote['pitch'] = pitch
    sgnote['stress'] = stress

    sg = trumpet.sound_generator_for(sgnote)
    sound = sg.render(pitch, length, note)
    normalize_amplitude(sound, stress)
    return sound

sound = forge_sound(float(argv[1]), 1, 0.8)

def write_file(fname):
    channels = ((x for x in sound),)
    write_wavefile(fname, channels, len(sound), 1, 2, 22050)
    print "Successfully written", fname, " – Please play with an appropriate command."

write_file(argv[2] or '/tmp/test.wav')

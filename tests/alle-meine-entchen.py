import sys, os
from Sompyler.synthesizer.sound_generator import SoundGenerator, Sympartial
from Sompyler.tone_mapper import get_mapper_from
from sine2wav import write_wavefile
import matplotlib.pyplot as plt
import numpy as np


mapper = get_mapper_from("test_examples/tones_euro_de+en.splt")()

soundgen = SoundGenerator.from_partial_spec_list([
   "1@100 A(.24:1,91;4,97;5,150;6,100) S(1.44:100;5,93;8,90;9,83;15,83;16,93;18,93) R(.8:100;10,89;93,0)",
   "2+3@82 A(.16:1,71;4,100) S(1.84:100;8,97;23,85) R(1.2:1;1,0)",
   "3+6@88 A(.16:1,76;4,100) S(2:100;6,91;9,79;13,93;22,96;24,70) R(1.22:70;4,78;39,0)",
   "4+10@71 A(.32:1,75;4,95;6,100) S(1.68:100;5,98;6,88;7,97;20,80;21,70) R(2.34:70;2,74;39,0)",
   "5+15@80 A(.16:1,73;4,100) S(1.76:100;6,87;7,78;8,76;9,89;16,100;22,94) R(.90:94;8,77;85,0)"
])

sound = np.array([])

def add_note (offset, pitch, length=1, stress=None):
    global sound
    print "Render note", offset
    offset = int(22050 * 3.0 * offset / 4.0)
    sound2 = soundgen.render( mapper(pitch), 3.0 * length / 4.0 )
    sound2 = np.append(
        np.zeros( offset ), sound2
    )
    if stress:
        sound2 *= stress
    lendiff = len(sound2) - len(sound)
    assert lendiff > 0
    sound  = np.append( sound, np.zeros( lendiff ) ) + sound2

add_note(0, "C4", 0.5, 1.5)
add_note(0.5, "D4", 0.5)
add_note(1.0, "E4", 0.5, 1.1)
add_note(1.5, "F4", 0.5)
add_note(2.0, "G4", 1.0, 1.2)
add_note(3.0, "G4", 1.0)

add_note(4.0, "A4", 0.5, 1.5)
add_note(4.5, "A4", 0.5)
add_note(5.0, "A4", 0.5, 1.1)
add_note(5.5, "A4", 0.5)
add_note(6.0, "G4", 2, 1.2)

add_note(8.0, "A4", 0.5, 1.5)
add_note(8.5, "A4", 0.5)
add_note(9.0, "A4", 0.5, 1.1)
add_note(9.5, "A4", 0.5)
add_note(10.0, "G4", 2, 1.2)

add_note(12.0, "F4", 0.5, 1.3)
add_note(12.5, "F4", 0.5)
add_note(13.0, "F4", 0.5, 1.05)
add_note(13.5, "F4", 0.5)
add_note(14.0, "E4", 1, 1.1)
add_note(15.0, "E4", 1)

add_note(16.0, "G4", 0.5, 1.3)
add_note(16.5, "G4", 0.5)
add_note(17.0, "G4", 0.5, 1.05)
add_note(17.5, "G4", 0.5)
add_note(18.0, "C4", 2, 1.1)

print "Sound rendered, now normalizing ..."
dmin = sound.min()
dmax = sound.max()
sound -= dmin
sound /= 0.5 * (dmax - dmin)
sound -= 1

print "Writing wave file ..."

def show_diagram(sound):
    plt.plot(sound)
    plt.show()

def write_file():
    channels = ((x for x in sound),)
    write_wavefile('/tmp/test.wav', channels, len(sound), 1, 2, 22050)

#show_diagram()
write_file()

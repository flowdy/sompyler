from Sompyler.synthesizer.sound_generator import SoundGenerator, Sympartial
from sine2wav import write_wavefile
import matplotlib.pyplot as plt
import numpy as np

soundgen = SoundGenerator.from_partial_spec_list([
   "1@100 A(.24:1,91;2,97;3,100) S(1.44:100;5,93;8,90;9,83;15,83;16,93;18,93) R(.8:100;10,89;93,0)",
   "2+3@83 A(.16:1,71;2,100) S(1.84:100;8,97;23,85) R(1.2:1;1,0)",
   "3+6@100 A(.16:1,76;2,100) S(2:100;6,91;9,79;13,93;22,96;24,70) R(1.22:70;4,78;39,0)",
   "4+10@86 A(.32:1,75;2,95;4,100) S(1.68:100;5,98;6,88;7,97;20,80;21,70) R(2.34:70;2,74;39,0)",
   "5+15@82 A(.16:1,73;2,100) S(1.76:100;6,87;7,78;8,76;9,89;16,100;22,94) R(.90:94;8,77;85,0)"
])

sound = np.array([])

def add_note (offset, pitch, stress=None, length=1):
    global sound
    print "Render note", offset
    sound2 = np.append(
        np.zeros( int(22050 * 2.66 * offset / 4.0) ),
        soundgen.render( pitch, 2.66 * length / 4.0 )
    )
    if stress:
        sound2 *= stress
    lendiff = len(sound2) - len(sound)
    assert lendiff > 0
    sound  = np.append( sound, np.zeros( lendiff ) ) + sound2

add_note(0, 391.995)

add_note(1, 329.628, 1.3)
add_note(2, 329.628)
add_note(3, 293.665, 1.1)
add_note(4, 293.665)

add_note(5, 261.626, 1.3)
add_note(6, 261.626)
add_note(7, 261.626, 1.1)
add_note(8, 391.995)

add_note(9, 440, 1.3)
add_note(10, 349.228)
add_note(11, 349.228, 1.1)
add_note(12, 440)

add_note(13, 391.995, 1.3, 3)
add_note(16, 391.995, 1.1)

add_note(17, 440, 1.3)
add_note(18, 391.995)
add_note(19, 440, 1.1)
add_note(20, 493.883)

add_note(21, 523.251, 1.3)
add_note(22, 391.995)
add_note(23, 391.995, 1.1)
add_note(24, 349.228)
add_note(25, 329.628, 1.3)
add_note(26, 329.628)
add_note(27, 293.665, 1.1)
add_note(28, 293.665)
add_note(29, 261.626, 1.3, 3)
    
print "Sound rendered, now normalizing ..."
dmin = sound.min()
dmax = sound.max()
sound -= dmin
sound /= 0.5 * (dmax - dmin)
sound -= 1

print "Writing wave file ..."

def write_file():
    channels = ((x for x in sound),)
    write_wavefile('/tmp/test.wav', channels, len(sound), 1, 2, 22050)

def show_diagram():
    plt.plot(sound)
    plt.show()

#show_diagram()
write_file()

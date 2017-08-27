from Sompyler.instrument import Variation
from Sompyler.tone_mapper import get_mapper_from
from sine2wav import write_wavefile
#import matplotlib.pyplot as plt
import numpy as np

mapper = get_mapper_from("test_examples/tones_euro_de+en.splt")()

piano = Variation.from_definition({
    "TYPE": "merge",
    "ATTR": "pitch",
    "R": ".04:100;3,78;2,0",
    "edb65p01": {
        'A': ".24:1,91;2,97;3,100",
        'S': "1.52:100;5,93;8,90;9,83;15,83;16,93;18,93;19,83"
    },
    "edb65p02": {
        'A': ".16;1,71;2,100",
        'S': "2.08:100;8,97;23,85;27,70;26,64",
    },
    "edb65p03": {
        'A': ".16;1,76;2,100",
        'S': "2.08:100;6,91;9,79;12,93;22,96;24,70;25,78;26,70",
    },
    "edb65p04": {
        'A': ".32:1,75;2,95;4,100",
        'S': "1.92:100;5,98;6,88;7,97;20,80;21,70;22,74;23,70",
    },
    "edb65p05": {
        'A': ".16:1,73;2,100",
        'S': "1.92:100;6,87;7,78;8,76;9,89;16,100;22,94;23,77;24,69",
    },
    "edb65p10": {
        # 10. 86 99 98 96 99 100 98 97 97 97 98 98 98 99 99 96 97 100 94 95 97 99 97 97 96 86
        'A': ".40:1,86;2,99;3,98;4,99;5,100",
        'S': "1.60:100;2,97;9,99;10,96;12,100;13,94;16,99;19,96;20,86",
    },
    "edb65p15": {
        # 15. 61 98 100 99 100 98 98 97 94 92 90 88 85 84 83 85 84 85 86 82 83 84 81 78 79 70 61
        'A': ".16:1,61;2,98;3,100",
        'S': "1.92:100;2,100;5,97;12,83;13,85;16,86;17,82;19,84;22,79;24,61",
    },
    "edb65p20": {
        # 20. 89 100 97 100 97 89 89 88 94 96 99 98 96 94 93 89 93 89 
        'A': ".16:1,89;2,100",
        'S': "1.12:100;1,97;2,100;4,88;7,99;13,93;14,89",
    },
    "edb65p25": {
        # 25. 80 100 98 95 91 89 88 88 87 85 80 80 81 81 81 80 85 81
        'A': ".16:1,80;2,100",
        'S': "1.12:100;4,89;8,85;9,80;15,85;16,81",
    },
    52: {
        "PARTIALS": [
            { 1: (74, "edb65p01") },
            { 3: (83, "edb65p02") },
            { 6: (100, "edb65p03") },
            { 10: (86, "edb65p04") },
            { 15: (82, "edb65p05") },
            { 21: 80 },
            { 27: 86 },
            { 34: 72 },
            { 41: 81 },
            { 49: (91, "edb65p10") },
            { 58: 87 },
            { 67: 93 },
            { 77: 90 },
            { 87: 96 },
            { 98: (77, "edb65p15") },
            { 110: 47 },
            { 121: 64 },
            { 134: 77 },
            { 147: 74 },
            { 160: (67, "edb65p20") },
            { 174: 79 },
            { 188: 79 },
            { 203: 65 },
            { 218: 62 },
            { 233: (74, "edb65p20") },
            { 250: 74 },
            { 266: 69 },
            { 283: 62 },
            { 300: 62 },
            { 318: 61 },
            { 336: 56 },
            { 355: 58 },
            { 374: 56 },
        ]
    }
    104: {
        "PARTIALS": [
            { 1: (99, "edb65p01") },
            { 3: (100, "edb65p02") },
            { 6: (100, "edb65p03") },
            { 10: (90, "edb65p04") },
            { 15: (94, "edb65p05") },
            { 21: 98 },
            { 27: 99 },
            { 34: 75 },
            { 41: 82 },
            { 49: (88, "edb65p10") },
            { 58: 80 },
            { 67: 76 },
            { 77: 89 },
            { 87: 90 },
            { 98: (79, "edb65p15") },
            { 110: 63 },
            { 121: 74 },
            { 134: 74 },
            { 147: 69 },
            { 160: (60, "edb65p20") },
            { 174: 67 },
            { 188: 79 },
            { 203: 64 },
            { 218: 62 },
            { 233: (60, "edb65p20") },
            { 250: 62 },
            { 266: 57 },
        ]
    },
    207: {
        "PARTIALS": [
            { 1: (94, "edb65p01") },
            { 3: (100, "edb65p02") },
            { 6: (98, "edb65p03") },
            { 10: (86, "edb65p04") },
            { 15: (85, "edb65p05") },
            { 21: 87 },
            { 27: 84 },
            { 34: 73 },
            { 41: 72 },
            { 49: (68, "edb65p10") },
            { 58: 67 },
            { 67: 64 },
            { 77: 63 },
            { 87: 58 },
            { 98: (56, "edb65p15") },
        ],
    },
    415: {
        "PARTIALS": [
            { 1: (100, "edb65p01") },
            { 3: (82, "edb65p02") },
            { 6: (88, "edb65p03") },
            { 10: (71, "edb65p04") },
            { 15: (80, "edb65p05") },
            { 21: 72 },
            { 27: 75 },
            { 34: 58 },
            { 41: 0 },
            { 49: (0, "edb65p10") },
        ],
    },
    4186: {
        'A': "0.03:1,100",
        'S': "4.8:100;1,95;10,0",
        'PARTIALS': [ 100, 75, 20, 15, 10 ]
    }
});

sound = np.array([])

def add_note (offset, pitch, length=1, stress=None):
    global sound
    print "Render note", pitch, offset
    offset = int(22050 * 3.0 * offset / 4.0)
    sound2 = soundgen.render( mapper(pitch), 3.0 * length / 4.0 )
    sound2 = np.append(
        np.zeros( offset ), sound2
    )
    if stress:
        sound2 *= stress
    lendiff = len(sound2) - len(sound)
    assert lendiff > 0
    sound = np.append( sound, np.zeros( lendiff ) ) + sound2

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
sound /= max(dmax, -dmin)
sound -= 1

print "Writing wave file ..."

def write_file():
    channels = ((x for x in sound),)
    write_wavefile('/tmp/test.wav', channels, len(sound), 1, 2, 22050)

write_file()

#show_diagram()
# def show_diagram(sound):
#     plt.plot(sound)
#     plt.show()


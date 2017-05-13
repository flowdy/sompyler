from Sompyler.synthesizer.oscillator import Oscillator
import matplotlib.pyplot as plt
import pdb
import numpy as np
from sine2wav import write_wavefile

osc = Oscillator(
    amplitude_modulation="5p;3:1,env:0;1,1;2,0",
    oscache={},
    wave_shape="0;4,99;7,70;9,100"
)

def write_file(sound):
    channels = ((x for x in sound),)
    write_wavefile('/tmp/test11.wav', channels, len(sound), 1, 2, 22050)

#pdb.set_trace()
rendered = osc(100.0/22050, 22050)
rendered /= rendered.max()
write_file(rendered)
# plt.plot(rendered)
# plt.show()

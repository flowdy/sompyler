from Sompyler.synthesizer.oscillator import CORE_PRIMITIVE_OSCILLATORS
import numpy as np
import matplotlib.pyplot as plt
from sine2wav import write_wavefile

cpo = CORE_PRIMITIVE_OSCILLATORS()
iseq = np.arange(22050)
noisegen = cpo[ ('noise',) ]( 'L3R9S5' )

for i in (20, 500, 7000, 13000, 20000): # 100,150,300,350,700,1400,2800,5600,11200,16500):
    r = noisegen(iseq, i)
    channels = (np.nditer(r),)
    write_wavefile('/tmp/test' + ('%05d' % i) + '.wav', channels, len(r), 1, 2, 22050)

# plt.plot(iseq, r)
# plt.show()

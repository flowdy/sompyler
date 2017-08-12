from Sompyler.synthesizer.oscillator import CORE_PRIMITIVE_OSCILLATORS
import numpy as np
import matplotlib.pyplot as plt
from sine2wav import write_wavefile

cpo = CORE_PRIMITIVE_OSCILLATORS()
iseq = np.arange(22050)
noisegen = cpo[ 'noise' ]

for i in (20,100,150,300,350,700,1400,2800,5600,11200,16500,20000):
    print "Write noise file of " + str(i) + "Hz ..."
    r = noisegen(i, iseq)
    channels = (np.nditer(r),)
    write_wavefile('/tmp/testb' + ('%05d' % i) + '.wav', channels, len(r), 1, 2, 22050)

# plt.plot(iseq, r)
# plt.show()

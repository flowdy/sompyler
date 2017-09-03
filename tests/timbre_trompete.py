import yaml, numpy
from sys import argv
from Sompyler.synthesizer.shape import Shape
from Sompyler.synthesizer.sound_generator import log_to_linear
from Sompyler.instrument import Variation
import matplotlib.pyplot as plt
import pdb

trumpet = yaml.load(open("instruments/dev-trumpet.spli", "r"))

timbre = Shape.from_string(trumpet['character']['TIMBRE'])

res = timbre.render( 1 )

plt.plot(range(len(res)), [ log_to_linear(x) for x in res ])
plt.show()

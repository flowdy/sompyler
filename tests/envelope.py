from Sompyler.synthesizer.envelope import Envelope
import matplotlib.pyplot as plt
import sys
# import pdb

curves = []
def render_curve (e):
    res = e.render(float(sys.argv[-1]))
    curves.append(range(len(res)))
    curves.append(res)

s2 = None
def render_curves_interpolate(a, b):
    global s2
    for i in 0.2, 0.4, 0.6, 0.8:
        # pdb.set_trace()
        s3 = Envelope.weighted_average(a, i, b)
        render_curve(s3)
    s2 = b
    render_curve(s2)

# Partial 1
render_curve(Envelope(".24:1,91;2,97;3,100", "1.44:100;5,93;8,90;9,83;15,83;16,93;18,93", release=".8:100;10,89;93,0"))

# Partial 2
render_curve(Envelope(".16:1,71;2,100", "1.84:100;8,97;23,85", release="1.2:1;1,0"))

# Partial 3
render_curve(Envelope(".16:1,76;2,100", "2:100;6,91;9,79;13,93;22,96;24,70", release="1.22:70;4,78;39,0"))

# Partial 4
render_curve(Envelope(".32:1,75;2,95;4,100", "1.68:100;5,98;6,88;7,97;20,80;21,70", release="2.34:70;2,74;39,0"))

# Partial 5
s2 = Envelope(".16:1,73;2,100", "1.76:100;6,87;7,78;8,76;9,89;16,100;22,94", release=".9:94;8,77;85,0")
render_curve(s2)

# Partials 6-10
render_curves_interpolate(
    s2, Envelope(".4:1,86;2,99;3,98;4,99;5,100", "1.52:100;2,97;9,99;10,96;12,100;13,94;16,99;19,96", release=".8:96;1,0")
)

# Partials 11-15
render_curves_interpolate(
    s2, Envelope(".16:1,61;2,98;3,100", "1.76:100;2,100;5,97;12,83;13,85;16,86;17,82;19,84;22,79", release=".89:100;1,0")
)

# Partials 16-20
render_curves_interpolate(
    s2, Envelope("0.16:1,89;2,100", "1.12:100;1,97;2,100;4,89;6,89;9,99;14,89", release="1.94:89;4,93;97,0")
)

# Partials 21-25
render_curves_interpolate(
    s2, Envelope(".16:1,80;2,100", "1.12:100;4,89;8,85;9,80;14,80", release="1.78:80;4,85;89,0")
)

plt.plot(*curves)
plt.legend( [ 'P' + str(i + 1) for i in range(len(curves)) ], fontsize="x-small" )
plt.savefig('/tmp/curves.png')



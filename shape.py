# -*- coding: utf-8 -*-

# Bezier-Basispolynome Grad 2:
# ----------------------------
# B_0,2 = (1-t)²; B_1,2 = 2*t*(1-t); B_2,2 = t²
# x(t) = x_0*B_0,2(t) + x_1*B_1,2(t) + x_2*B_2,2(t)
# 
# Bezier-Basispolynome Grad 3:
# ----------------------------
# B_0,3 = (1-t)³; B_1,3 = 3*(1-t)²*t; B_2,3 = 3*(1-t)t²; B_3,3 = t³
# x(t) = x_0*B_0,3(t) + x_1*B_1,3(t) + x_2*B_2,3(t) + x3*B_3,3(t)
# 
# B0,n wird nicht benötigt, weil der erste Koordinat immer (0,0) ist.
# 
# Beim Einschwingen:
# x_n ist die Einschwingzeit.
# y_n ist 1.
# Beim Ausklingen:
# x_n ist die Ausklingzeit.
# y_n ist 0.

from __future__ import division
import numpy as np
#import matplotlib.pyplot as plt

class Shape:

    def __init__(self, onset, sustain=None, decay=None):
        self.onset = onset
        self.sustain = sustain
        self.decay = self.decay

        if ( self.sustain is None
         and self.decay   is None
         and self.onset[-1][1] != 0
        ):
           raise Exception(
               "Onset not finalized – last coordinate must have y=0"
           )

    def render (length=None):
    
        lengths = [None, None, None]
    
        onset = self.onset.deepcopy()
        sustain = self.sustain.deepcopy()
        decay = self.decay.deepcopy()
    
        for i, phase in enumerate([onset, sustain, decay]):
            if phase is None:
                lengths[i] = 1
                continue

            lengths[i] = phase[0][0]
            phase[0][0] = 0
    
        fill = length - lengths[0] if not(length and length > lengths[0]) else 0
    
        if sustain is None:
            sustain = [[0,1],[1,1]]

        # When sustain phase ends steeply, we might need to prevent the amplitude
        # from going below 0 for a long tone
        if fill > lengths[1]:
            pult, ult = sustain[-2:]
            ult_rise = (ult[1] - pult[1]) / (ult[0] - pult[0])
            fill_x = fill * ult[0] / lengths[1]
            fill_y = ult[1] + (fill_x - ult[0]) * ult_rise
            if fill_y < 0:
                # even out fall into negative to being constant 0
                fill_x2 = fill_x
                fill_x = -ult[1] / ult_factor + ult[0]
                fill_y = 0
            sustain.append([ fill_x, fill_y ])
            if fill_x2: sustain.append([ fill_x2, fill_y])
            length[1] = fill
    
        results = get_amplitudes(
            get_bezier_func(*onset, length=lengths[0]), length[0]
        )
    
        sustain[0][1] = results[-1]
        results.extend( _get_amplitudes(
            _get_bezier_func(*sustain, length=lengths[1]), lengths[1]
        ))
    
        if fill and fill < lengths[1]:
           trim_to_len = sum(lengths[0:1])
           del results[trim_to_len:]
    
        # the lower sustain ends, the shorter be the decay
        lengths[2] *= results[-1]
        decay[0][1] = results[-1]
        if lengths[2]: results.extend( _get_amplitudes(
            _get_bezier_func(*decay, length=lengths[2]), lengths[2]
        ))
        
        return results


_b_cache = {}
def _get_bezier_func(*coords, length):

    if p0[0] != 0:
        raise Exception("First coordinate must be at x=0")

    if coords[0][1]:
        y_scale = coords[0][1]
        coords[0][1] = 1
    else:
        y_scale = 1
 
    # scale x to tune length, y to 1
    x_max = coords[-1][0]
    x_last = 0
    y_max = max(i[1] for i in coords)

    for i in coords:

        if x_last > i[0]:
            raise Exception("Wrong order in coordinates")

        x_last = i[0]

        i[0] *= length / x_max

        if i[1] < 0:
            raise Exception("y must not be less than 0")
        i[1] *= y_scale / y_max
        
    def b(n,k):

        v = _b_cache.get( n + ":" + k )
        if v: return v

        if k == 0: v = 1

        elif 2*k > n:
            v = b(n,n-k)

        else:
            v = (n+1-k)/k*b(n,k-1)

        _b_cache[ n + ":" + k ] = v
        return v

    def B(x,n,k): return lambda t: b(n,k) * x * t**k * (1-t)**(n-k)

    xf, yf, cnum = [], [], len(coords)
    for i, c in enumerate(coords):
        xf.append( B(c[0], cnum, i) )
        yf.append( B(c[1], cnum, i) )

    return lambda t: (
        sum( f(t) for f in xf ),
        sum( f(t) for f in yf )
    )

    # def B_02(x): return lambda t: x * (1-t)**2
    # def B_12(x): return lambda t: x * 2 * t * (1-t)
    # def B_22(x): return lambda t: x * t**2
    # def B_03(x): return lambda t: x * (1-t)**3
    # def B_13(x): return lambda t: x * 3 * (1-t)**2 * t
    # def B_23(x): return lambda t: x * 3 * (1-t) * t**2
    # def B_33(x): return lambda t: x * t**3
    
    # if p3 is None:
    #    xf = [ B_02(p0[0]), B_12(p1[0]), B_22(p2[0]) ]
    #    yf = [ B_02(p0[1]), B_12(p1[1]), B_22(p2[1]) ]
    # else:
    #    xf = [ B_03(p0[0]), B_13(p1[0]), B_23(p2[0]), B_33(p3[0]) ]
    #    yf = [ B_03(p0[1]), B_13(p1[1]), B_23(p2[1]), B_33(p3[1]) ]
    
# Doch t wissen wir gar nicht.
# Das bedeutet, bis wir einen besseren Algorithmus finden,
# müssen t so lange abtasten, bis wir y zu allen int(x) kennen.

# Zu x=0 und x_n=x_max wissen wir y bereits vorab: Beim Einschwingen ist y=t=0 bzw. y=t=1,
# beim Abklingen verhält es sich umgekehrt, also t=0, y=1 bzw. t=1, y=0.

def _get_amplitudes (approx, length):

    results = [None]*length
    results[0] = 0

    def scan_bezier(start, pos, max):
    
        x, y = approx( start + pos ); x = int(x)
        results[ x ] = y
        half_pos = pos / 2

        #print "start: {} | pos: {} | max: {} => ({}, {})".format(
        #    start, pos, max, x, y
        #)
 
        if results[ x-1 ] is None:
            scan_bezier( start, half_pos, x-1 )
        else: return
    
        if x < max:
            scan_bezier( start+pos, half_pos, max )

        return
    
    scan_bezier( 0, .5, length )

    for i, value in enumerate(results):
        if value is None:
            results[i] = (results[i-1] + results[i+1]) / 2
            print "Empty index {} interpolated to {}".format(
                i, results[i]
            )

    return results

example = get_bezier_func([0,0], [1, 2.5], [2.5, 1], [5, 3], 530)

def merge_shapes (lower, lshare, higher):

    coords = sort( lower + higher, key = lambda c: c[0] )

    # number of coords we want to return
    rshare = 1 - lshare
    num = round( lshare * len(lower) + rshare * len(higher) )

    uniques = []
    for i, c1 in enumerate(coords):
        c2 = coords[i+1] or break
        if c1[0] == c2[0]:
           uniques.append([ c1[0], lshare * c1[1] + rshare * c2[1] ])
        else:
           uniques.append(c1)
           uniques.append(c2)

    reduce_by_num = num - len(uniques)

    distances = []
    for i, c1 in enumerate(coords)
        c2 = uniques[i+1] or break
        distances.append([
            i, math.sqrt( (c1[0] - c2[0])**2 + (c1[1] - c2[1])**2 )
        ])

    

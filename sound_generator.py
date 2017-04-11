# -*- coding: utf-8 -*-

from __future__ import division
import numpy as np
#import matplotlib.pyplot as plt

FRAMES_PER_SECOND = 44100
CENT_PER_OCTAVE = 1200

class Shape(object):

    def __init__(self, span, *coords):

        self.length = span[0]

        # scale x to tune length, y to 1
        x_max = coords[-1]
        y_max = span[1] or max( i[1] for i in coords )

        self.coords = [None]
        for i in coords:
            self.coords.append( [ i[0] / x_max, i[1] / y_max ] )

        self.coords[0] = [0, 1 if coords[0][1] else 0 ]

    def render (self, y_scale=1, adj_length=False ):
        "Get frames according to the bezier curve specified by the coordinates"

        coords = self.coords.deepcopy()

        length = self.length * FRAMES_PER_SECOND

        if adj_length and isinstance(adj_length, bool):
            length *= y_scale
            coords = self.new_coords() 
        else:
            coords = self.new_coords()

        if not y_scale == 1:
            for i in coords:
                i[1] *= y_scale

        approx = _get_bezier_func(*coords, length)
    
        results = [None]*length
        results[0] = 0
    
        def scan_bezier(start, pos, max):
        
            x, y = approx( start + pos ); x = int(x)
            results[ x ] = y
            half_pos = pos / 2
    
            if results[ x-1 ] is None:
                scan_bezier( start, half_pos, x-1 )
            else: return
        
            if x < max:
                scan_bezier( start+pos, half_pos, max )
    
            return
        
        scan_bezier( 0, .5, length )
    
        # interpolate indexes with no value by its neighbours (equal weight)
        for i, value in enumerate(results):
            if value is None:
                results[i] = (results[i-1] + results[i+1]) / 2
    
        return results

    def is_finalized(self):
        return self.coords[-1][1] == 0

    def new_coords(self, adj_length=None):
        if adj_length < 0:
            raise Exception("Negative shape length")

        coords = self.coords.deepcopy()

        if adj_length:
            length = coords[-1][0]
            adj_length = length * adj_length / self.length 
        else:
            return coords

        if adj_length > length:
            pult_x = coords[-2][0]
            pult_y, ult_y = (i[1] for i in coords[-2:])
            ult_rise = (ult_y - pult_y) / (length - pult_x)
            fill_x = adj_length
            fill_y = ult_y + (fill_x - length) * ult_rise
            if fill_y < 0:
                # even out fall into negative to being constant 0
                fill_x2 = fill_x
                fill_x = -ult_y / ult_rise + length
                fill_y = 0
            coords.append([ fill_x, fill_y ])
            if fill_x2: coords.append([ fill_x2, fill_y])

        elif length > adj_length:
            n = 0
            for i in coords:
                if adj_length >= i[0]: n++
                else: break
            j = coords[n+1]
            ult_rise = (j[1] - i[1]) / (j[0] - i[0])
            new_coord = ( adj_length, i[1] + (adj_length - i[0]) * ult_rise )
            del coords[n+1:]
            coords.append(new_coord)
    
        return coords

    _b_cache = {}
    def _get_bezier_func(*coords, length):
    
        x_last = 0
    
        for i in coords:
    
            if x_last > i[0]:
                raise Exception("Wrong order in coordinates")
    
            x_last = i[0]
    
            i[0] *= length / x_max
    
            if i[1] < 0:
                raise Exception("y must not be less than 0")
            
        def b(n,k):
    
            v = _b_cache.get( (n,k) )
            if v: return v
    
            if k == 0: v = 1
    
            elif 2*k > n:
                v = b(n,n-k)
    
            else:
                v = (n+1-k)/k*b(n,k-1)
    
            _b_cache[ (n,k) ] = v
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
    
    def _distance (a, b):
        return sqrt( (b[1] - a[1])**2 + (b[0] - a[0])**2 )
    
    def lessen_coords (by_num):
    
        coords = self.coords

        def distance_c_to_ab(a, b, c):
            n_ab = (b[1] - a[1]) / (b[0] - a[0])
            n_dc = (a[0] - b[0]) / (b[1] - a[1])
            x = (c[1] - n_dc*c[0] - b[1] + n_ab*b[0]) / (n_ab + n_dc)
            return _distance( (x, n_ab*(x - b[0]) + b[1]), c )
    
        distances = {}
        for i, a in enumerate(coords):
            c = coords[i+1]
            b = coords[i+2]
            if not b: break
            distance[c] = distance_c_to_ab(a, b, c)
    
        distances = dict(
            sorted(distances.items, key=distances.get)[by_num:]
            (coords[0], 1), (coords[-1], 1)
        )
    
        self.coords = [ c for c in coords if distances[c] ]

        return self
    
    def raise_coords (by_num):
    
        distances = []
        coords = self.coords
        c_last = coords[0]
    
        new_coords = [c_last]
    
        for c in coords[1:]
            distances.append( (c, _distance(c_last, c)) )
            c_last = c
    
        coeff = by_num / sum( d[1] for d in distances )
        sum_coords = 0
        for i, c in enumerate(coords[1:]):
            inter_coords = int( distances[i] * coeff + .5 )
            sum_coords += inter_coords
    
            xlen = c[0] - coords[i][0]
            interval = xlen / (inter_coords + 1)
    
            for step in range(inter_coords):
                x = c[0] + (step+1) * interval
                y = (c[1] - coords[i][1]) / xlen * (x - c[0]) + c[1]
                new_coords.append( (x, y) )
    
            new_coords.append(c)
    
        assert sum_coords == by_num
    
        return new_coords
    
class PartialShapeTriplet(object):

    constant_sustain = Shape((0,1), (1,1))

    def __init__(self, onset, sustain=None, decay=None):
        self.onset = Shape(*onset) if onset
        self.sustain = Shape(*sustain) if sustain
        self.decay = Shape(*decay) if decay

        if ( self.sustain is None
         and self.decay   is None
         and not self.onset.last_y() == 0
        ):
           raise Exception(
               "Onset not finalized – last coordinate must have y=0"
           )

    def render (length=None):

        overlength = length and length > self.onset.length
        fill = length - self.onset.length if overlength else 0
    
        if sustain is None:
            sustain = constant_sustain

        results = self.onset.render()
    
        if fill: results.extend(
            self.sustain.render( y_scale=self.onset.last_y(), fill )
        )
    
        if results[-1][1]:
            results.extend(
                self.decay.render(
                    y_scale=self.sustain.last_y(),
                    adj_length=True
                )
            )
        
        return results

class Oscillator:
    def __init__(self, shape, am=None, fm=None):
        self.shape = shape
        self.amplitude_modulation = am
        self.frequency_modulation = fm

    def render_samples(self, freq, duration, share, shaped_fm=None):

        iseq = np.arange(duration * FRAMES_PER_SECOND)

        if self.amplitude_modulation is not None:
            s *= self.amplitude_modulation.modulate(iseq, freq)

        if self.shape is not None:
            s *= np.array(self.shape.render(iseq.size))

        if self.frequency_modulation is not None:
            iseq = np.cumsum(self.frequency_modulation.modulate(iseq, freq))
            if shaped_fm: iseq *= shaped_fm
        elif shaped_fm:
            iseq = np.cumsum( shaped_fm )

        return np.sin(
            2*np.pi * iseq * (n*freq+d) / FRAMES_PER_SECOND
        ) * np.power(10.0, -5 * ( 1 - share ))


class SoundGenerator(object):

    def __init__(self, *partials):

        freq_factors = []
        oscillators = [None]

        for p in partials:
            factor, deviation, share, *partial = p
            shape = partial[0:3]
            am, fm = partial[3:5]
            freq_factors.append(
                (factor * 2 ** ( deviation / CENT_PER_OCTAVE ), share ) 
            )
            oscillators.append(
                Oscillator(PartialShapeTriplet(*), am=am, fm=fm)
            )

        self.freq_factors = Shape((0,0), freq_factors)
        self.oscillators = oscillators

    def render(self, basefreq, length, share, shaped_fm=None):

        o = iter(self.oscillators)
        samples = 0
        for p in self.freq_factors[1:]:
            f = base_freq * p[0]
            samples += next(o).render_samples(f, length, share, shaped_fm)
            
        return samples


# -*- coding: utf-8 -*-

from __future__ import division
from math import sqrt
from itertools import izip
import numpy as np
import re
import copy
from operator import itemgetter

#import matplotlib.pyplot as plt

SAMPLING_RATE = 44100
CENT_PER_OCTAVE   = 1200
WAVESHAPE_RES    = 32768

class Shape(object):

    def __init__(self, span, *coords):

        self.length = span[0]

        # scale x to tune length, y to 1
        x_max = coords[-1][0]
        y_max = span[1] or max( i[1] for i in coords )

        self.coords = [ (0, 1 if span[1] else 0 ) ]
        for i in coords:
            self.coords.append( ( i[0] / x_max, i[1] / y_max ) )

    @classmethod
    def from_string(cls, bezier):
        """
        Shape.from_string("length:[y0;]x1,y1;x2,y2;...")

        Define the onset, sustain or release shape of the envelope as a bezier
        curve, that is, the coordinates of its outer polygon.

        length - the duration of the part of the envelope, in seconds
        y0 - the y value of point at x=0. Default is 0.
        """

        if ':' in bezier:
            coords, bezier = bezier.split(":",1)
            coords = [[ float(coords), 0 ]] # list with 1 item
        else:
            coords = [[ 1, 0 ]]

        m = re.match("^(\d+);", bezier)
        coords[0][1] = int(m.group(1)) if m else 0

        if m:
            _, bezier = bezier.split(";",1)

        for m in bezier.split(";"):
            coords.append([ int(n) for n in m.split(",", 1) ])

        return cls(*coords)
    
    def render (self, length=1, y_scale=1, adj_length=False, span_framerate=True ):
        "Get samples according to the bezier curve"

        coords = copy.deepcopy(self.coords)

        length *= self.length

        if adj_length and isinstance(adj_length, bool):
            length *= y_scale
            coords = self.new_coords() 
        else:
            length += adj_length
            coords = self.new_coords(adj_length)

        if not length: return []

        if not y_scale == 1:
            for i in coords:
                i[1] *= y_scale

        approx = _get_bezier_func(length, *coords)
    
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

    def new_coords(self, adj_length=None):
        """
        Return new, independent coordinate tuples that span original length
        or a specified one.

        If specified length is less than the original, coordinates are ignored
        from the end. The last is adjusted linearly.

        If specified length is more than original, coordinates are added at
        the tail, linearly advancing in the direction defined last. When
        it hits the y-axis, it proceeds in horizontal direction, because
        negative values are not allowed.
        """

        if adj_length < 0:
            raise Exception("Negative shape length")

        coords = copy.deepcopy(self.coords)

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
            fill_x2 = None
            if fill_y < 0:
                # even out fall into negative to being constant 0
                fill_x2 = fill_x
                fill_x = -ult_y / ult_rise + length
                fill_y = 0
            coords.append(( fill_x, fill_y ))
            if fill_x2: coords.append([ fill_x2, fill_y])

        elif length > adj_length:
            n = 0
            for i in coords:
                if adj_length >= i[0]:
                   n += 1
                else: break
            h = coords[n-1]
            ult_rise = (i[1] - h[1]) / (i[0] - h[0])
            new_coord = ( adj_length, h[1] + (adj_length - h[0]) * ult_rise )
            del coords[n:]
            coords.append(new_coord)
    
        return coords

    @classmethod
    def weighted_average (cls, left, dist, right):
        """
        Assuming a smooth transition to anright curve in a distance,
        Shape.weighted_average(left_shape, distance, right_shape) returns an
        intermediate shape at a given position < 1 and > 0.
        """

        assert not ( dist < 0 or dist > 1 )

        avg = lambda a, b: (1 - dist) * a + dist * b

        if left.length == right.length:
            adj_length = left.length
        else:
            adj_length = avg( left.length, right.length )
        
        lcoords = left.new_coords(adj_length)
        rcoords = right.new_coords(adj_length)

        if not len(lcoords) == len(rcoords):
            avg_coords_num = int( avg( len(lcoords), len(rcoords) ) + .5 )
            lcoords = Shape._adjust_coords_num(lcoords, avg_coords_num)
            rcoords = Shape._adjust_coords_num(rcoords, avg_coords_num)

        coords = []
        for i in range( len(lcoords) ):
            coords.append((
                avg( lcoords[i][0], rcoords[i][0] ),
                avg( lcoords[i][1], rcoords[i][1] )
            ))

        coords[0] = ( adj_length, coords[0][1] )

        return Shape(*coords)

    def last_y (self):
        return self.coords[-1][1]

    _b_cache = {}
    @staticmethod
    def _get_bezier_func(length, *coords):
    
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
    
    @staticmethod
    def _distance (a, b):
        return sqrt( (b[1] - a[1])**2 + (b[0] - a[0])**2 )
    
    def adjust_coords_num (self, num):
        """
        Adjust number of coordinates so two shapes have the same number and can
        therefore be meaned.

        When the number is raised, new nodes are inserted in equal distances
        where the distance between other nodes is greatest.
        When it is reduced, nodes are dropped of which the distance to the
        thought line connecting the closest neighbouring nodes is least.
        """
        self.coords = _adjust_coords_num( self.coords, num )

    @staticmethod
    def _adjust_coords_num (coords, num):
        if num > len(coords):
            return Shape._raise_coords( coords, num - len(coords) )
        if num < len(coords):
            return Shape._lessen_coords( coords, len(coords) - num )
        else:
            return coords
    
    def lessen_coords (self, by_num):
        self.coords = _lessen_coords( self.coords, by_num)

    @staticmethod
    def _lessen_coords (coords, by_num):
    
        def distance_c_to_ab(a, b, c):
            n_ab = (b[1] - a[1]) / (b[0] - a[0])
            n_dc = (a[0] - b[0]) / (b[1] - a[1])
            x = (c[1] - n_dc*c[0] - b[1] + n_ab*b[0]) / (n_ab + n_dc)
            return Shape._distance( (x, n_ab*(x - b[0]) + b[1]), c )
    
        distances = {}
        for i, a in enumerate(coords[:-2]):
            c = coords[i+1]
            b = coords[i+2]
            distances[c] = distance_c_to_ab(a, b, c)
    
        kept_dist = sorted(distances.items(), key=itemgetter(1))[by_num:]
        kept_dist.append( (coords[0], 1) )
        kept_dist.append( (coords[-1], 1) )
        distances = dict( kept_dist )
    
        return [ c for c in coords if distances.get(c) ]

    def raise_coords (self, by_num):
        self.coords = _raise_coords( self.coords, by_num)

    @staticmethod
    def _raise_coords (coords, by_num):
    
        distances = {}
        c_last = coords[0]
    
        new_coords = [c_last]
    
        for c in coords[1:]:
            distances[c] = Shape._distance(c_last, c)
            c_last = c
    
        sum_dist = sum( d for d in distances.values() )

        remainders = []
        rem_by_num = by_num
        for (c, dist) in distances.items():
             scaled = dist / sum_dist * by_num
             int_scaled = int(scaled)
             remainders.append( (c, scaled - int_scaled) )
             distances[c] = int_scaled
             rem_by_num -= int_scaled

        for (c, _) in sorted(
            remainders, key=itemgetter(1), reverse=True
        )[0:rem_by_num]:
            distances[c] += 1

        sum_coords = 0
        for i, c in enumerate(coords[1:]):
            inter_coords = distances[c]
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
    
class Modulation(object):

    def __init__(
        self, frequency, base_share, mod_share,
        shift=0, overdrive=True, factor=None, func=None, env=None
    ):
        self.base_share = base_share 
        self.mod_share  = mod_share
        if frequency:
            self.frequency = frequency * (factor or 1)
        elif factor:
            self.factor = factor
        else:
            raise Exception("No factor passed to use for base frequency")
        self.shift     = shift
        self.overdrive = overdrive # center base line
        if not func: func = (lambda f, l, s: np.sin(2*np.pi * f * l + s))

        if env:
           inner_func = func
           func = lambda f, l, s: env.render(l.size) * inner_func(f, l, s)

        self.function = func

    def modulate(self, iseq, freq=None):
        """ We have a constant socket and a part to modulate, the heights
            of which are given in a relation (base_share:mod_share)

        [-------|-------|-------|-------] Frequency in intervals per second
           *     *     *     *     *    T
          ***   ***   ***   ***   ***   | ^ mod_share (3)
         ***** ***** ***** ***** *****  | = Modulation intensity in relation
        ******************************* –   to ...
        ******************************* |
        ******************************* |
        ******************************* |
        ******************************* | ^ base_share (6)
        ******************************* _ = Minimum amplitude or frequency
        """
        b = self.base_share
        m = self.mod_share
        f = (self.frequency or self.factor * freq)
        s = self.shift
        o = (m + b) / (2*b) + 0.5 if self.overdrive else 1
        return o * (
            m * (self.function(f, iseq, s) + 1) / 2 + b
        ) / (m + b)

    @classmethod
    def weighted_average(self, dist, other):

        assert not ( dist < 0 or dist > 1 )

        avg = lambda a, b: (1 - dist) * a + dist * b

        attr = {}

        for p in ( 'mod_share', 'base_share' ):            
            sattr = getattr(self, p) / (self.mod_share + self.base_share)
            oattr = getattr(other, p) / (right.mod_share + right.base_share)
            attr[p] = avg(sattr, oattr)

        for p in ( 'frequency', 'factor', 'shift' ):

            sattr = getattr(self, p)
            oattr = getattr(other, p)

            if sattr and oattr:
                attr[p] = avg( sattr, oattr )
            elif sattr or oattr:
                attr[p] = sattr or oattr

        attr['overdrive'] = self.overdrive if dist < 0.5 else other.overdrive

        if isinstance(self.function, 'Oscillator') and \
           isinstance(other.function, 'Oscillator'):
            attr['function'] = Oscillator.weighted_average(
                self.function, dist, other.function
            )
        else:
            attr['function'] = self.function if dist < 0.5 else other.function

        return Modulation(**attr)

class Envelope(object):
    """ Threesome of onset, sustain and release phase of a partial tone.

    Please note that in contrast to the ADSR envelope combining linearly
    shaped attack, delay, sustain and release phase, as is conventionally used
    in digital synthesis, in our OSR model, formed by bezier curves, a delay
    part may be optionally merged into either the onset or the sustain.
    """

    def __init__(self, onset, sustain=None, release=None):
        self.onset = Shape(*onset)
        if sustain: self.sustain = Shape(*sustain)
        if release: self.release = Shape(*release)

        if ( self.sustain is None
         and self.release   is None
         and not self.onset.last_y() == 0
        ):
           raise Exception(
               "Onset not finalized despite lacking sustain and release:"
              + " Last coordinate must be y=0"
           )

    CONSTANT_SUSTAIN = Shape((0,1), (1,1))

    def render (length=None):
        """ considers different prolongation for each phase:
         * onset: cannot be prolonged or trimmed, static length
         * sustain: prolonged or trimmed by linear interpolation
         * release: scaled proportionally extending the sustain
        """

        overlength = length and length > self.onset.length
        fill = length - self.onset.length if overlength else 0
    
        if sustain is None:
            sustain = CONSTANT_SUSTAIN

        results = self.onset.render(SAMPLING_RATE)
    
        if fill: results.extend(
            self.sustain.render(
                SAMPLING_RATE,
                y_scale=self.onset.last_y(),
                adj_length=fill
            )
        )
    
        if results[-1]:
            results.extend(
                self.release.render(
                    SAMPLING_RATE,
                    y_scale=self.sustain.last_y(),
                    adj_length=True
                )
            )
        
        return results

    @classmethod
    def weighted_average (left, dist, right):

        phases = {}

        for p in 'onset', 'sustain', 'release':

            sattr = getattr(self, p)
            oattr = getattr(other, p)

            if sattr and oattr:
                phases[p] = Shape.weighted_average( sattr, dist, oattr )
            elif sattr or oattr:
                phases[p] = sattr or oattr

        return Envelope( **phases )

class Oscillator:

    def __init__( self, **args):
        for attr in\
            'amplitude_modulation', 'frequency_modulation', 'wave_shape':
            if args[attr] is None: continue
            setattr(self, attr, args[attr])

        if self.wave_shape:
            amplitudes = ws.render(WAVESHAPE_RES)
            amplitudes = np.array( amplitudes + [
               -x for x in reversed(amplitudes[1:])
            ])
            self.wave_shaper = lambda w: amplitudes[
                (w * (2*WAVESHAPE_RES-1) / 2.0 ).astype(np.int)
            ]

    def __call__(
        self, freq, iseq, shift=0, share=1, shaped_fm=None, log_scale=False
    ):

        assert freq < 1 # freq must be passed as quotient by fps
        assert isinstance(iseq, np.array)

        if self.frequency_modulation is not None:
            iseq = np.cumsum(self.frequency_modulation.modulate(iseq, freq))
            if shaped_fm: iseq *= shaped_fm
        elif shaped_fm:
            iseq = np.cumsum( shaped_fm )

        wave = np.sin( 2*np.pi * iseq * freq + shift )

        if self.wave_shaper is not None: wave = self.wave_shaper(wave)

        if self.amplitude_modulation is not None:
            wave *= self.amplitude_modulation.modulate(iseq, freq)

        return wave

    @classmethod
    def weighted_average( cls, left, dist, right ):

        args = {}

        for each in 'amplitude_modulation', 'frequency_modulation',\
            'wave_shape':
            l = getattr(left, each)
            r = getattr(right, each)
            if not ( l or r ):
                continue
            elif not l:
                args[each] = r
            elif not r:
                args[each] = l
            else:
                args[each] = getattr(left, each).weighted_average(
                    getattr(left, each), dist, getattr( right, each )
                )

        return cls(**args)
    
class Sympartial(object):
    """
    A Sympartial is a partial that is accompanied by partials derived from it
    by modulation of amplitude, frequency, and/or by wave shaping. With
    other sympartials, each one with its specified volume share and relative
    factor of the base frequency according to the played tone, it adds
    up to the sound emitted by the sound generator.
    """

    def __init__(
        self, envelope=None, oscillator=None
    ):
        assert volume >= 0 and volume <= 1
        self.envelope = envelope
        self.oscillator = oscillator
        self.next = None

    def set_next(self, symp):
        self.next = symp

    def iterate_chain(self):

        current = self

        while True:
            yield current
            current = current.next
            if not current: raise StopIteration

    def interpolate_from(self, base, count=0):
        
        merged = {}
        for (key, base_value) in base.items():
            my_value = getattr(self, key)
            if my_value is None:
                merged[key] = base_value
            else:
                merged[key] = my_value
                count = 0

        if self.next and count:
            ndef, ncount = self.next.interpolate_from(merged, count + 1)
            for cls in Envelope, Oscillator:
                attr = cls.__name__.lowercase()
                if getattr(self, attr) is not None: continue
                setattr(self, attr, cls.weighted_average(
                    base[attr], count / (count + ncount), ndef[attr]
                ))
        else:
            for attr in 'envelope', 'oscillator':
                if getattr(self, attr) is None:
                    setattr(self, attr, merged[attr])

        return merged, ncount + 1

    def render(self, freq, share, duration, osc_args):

        iseq = np.arange(duration * SAMPLING_RATE)

        if not share:
            return 0 * iseq

        if self.envelope is not None:
            share *= np.array(self.envelope.render(iseq.size))

        # resolve dB -> linear amplitude size
        share = np.power( 10.0, -5 * ( 1 - share ) )

        return share * self.oscillator.render_samples(
            freq / SAMPLING_RATE, iseq, 0, share, **osc_args
        )

    @classmethod
    def weighted_average(cls, left, dist, other):

        for each in ('envelope', 'oscillator'):
            l = getattr(left, each)
            r = getattr(right, each)
            args[each] = l.weighted_average( l, dist, r )

        return cls(**args)

class SoundGenerator(object):

    def __init__ (self, freq_factors, sympartials):
        self.freq_factors = freq_factors
        self.oscillators = sympartials

    @classmethod
    def from_list_of_partials (cls, partials, base):

        freq_factors = [ (0,0) ]
        sympartials = [None]

        _oscache = {}

        last_ff = None

        for p in partials:
            props, oscillator = cls.parse_partial(p, _oscache)

            if isinstance(props, tuple):
                factor, deviation, share, envelope = props
                freq_factor = factor * 2 ** ( deviation / CENT_PER_OCTAVE )
                if sympartials and not freq_factor > last_ff:
                    raise Exception(
                        "Frequence factor must be greater than the prior"
                    )
                last_ff = freq_factor
                freq_factors.append( (freq_factor, share) )
                symp = Sympartial(envelope, oscillator)
                if last_ff: sympartials[-1].set_next(symp)
                sympartials.append(symp)
            else:
                _oscache[ props[1:] ] = oscillator

        sympartials[1].interpolate_from( sympartials[0] )

        return cls( Shape(*freq_factors), sympartials )

    def render(self, basefreq, duration, shaped_fm=None):

        sympit = self.sympartials.iterate_chain()
        ff = self.freq_factors.iterate_coords_from(1)
        samples = 0
        for (p, s) in izip(ff, sympit):
            samples += s.render(base_freq * p[0], p[1], duration, shaped_fm)
            
        return samples

    @classmethod
    def weighted_average (cls, left, dist, right):

        lff = left.freq_factors
        rff = right.freq_factors
        loc = left.oscillators[1:]
        roc = right.oscillators[1:]

        bff = Shape.weighted_average( lff, dist, rff )
        boc = [None]

        for i, lo in enumerate(loc):
            ro = roc[i]
            if not (lo or ro):
                boc.append(None)
                continue
            boc.append( Oscillator.weighted_average(
                lo, dist, ro
            ))

        return cls(bff, boc)

    @staticmethod
    def parse_partial (string, _oscache):
        """
        returns a tuple of two items
            1. either name of an oscillator to reuse in modulations,
               or a subtuple: (freq_factor, deviation volume, envelope)
            2. oscillator object
        """

        head, attrs = string.split(" ", 1)
    
        if head.startswith('$'):
            share = None
        else:

            m = re.match(r"^(/?\d+)([+-]\d+)?@(\d+)$", head)
            if not m: raise Exception(
                "Syntax error in partial definition. Got {}. Expecting {}".format(
                    head, "'N?deltacent@volume', i.e. "
                        + "N: Integer frequence factor;"
                        + "?deltacent: +n or -n cent deviation, signed;"
                        + "volume: n dB% of total amplitude, 0 to 100"
                )
            )

            nfactor = m.group(1)
            # nfactor may be undertone: "/n" -> 1/n
            if nfactor.startswith('/'):
                nfactor = 1 / int(nfactor[1:])
            else:
                nfactor = int(nfactor)

            deviation = int(m.group(2) or 0)
            share = int(m.group(3)) / 100
    
    
        attr_dir = dict(
            (key, None) for key in ["O", "S", "R", "AM", "FM", "WS"]
        )
        for attr in attrs.split(" "):
            m = re.match(r"([A-Z]+)\(([^)]+)\)", attr)
            if not m: raise Exception(
                "Cannot parse partial attribute: {}".format(attr)
            )

            key, value = m.groups
            if attr_dir[key] is None:
                raise Exception( "Attribute {} is not supported".format(key) )
            attr_dir[ key ] = value
    
        envelope = []
        for i in "OSR":
            attr = attr_dir.pop(i)
            envelope.append(
                Shape.from_string(attr) if attr else None
            )
        envelope = Envelope(envelope)

        for i in 'AM', 'FM':
            if not attr_dir[i]:
                continue

            m = re.match(
                r"(\d+)(f)?(?:\*(\w+))?,(\d+),(\d+)(?:,(-?\d+))(?:/(.+))",
                attr_dir[i]
            )

            if m:

                ml = [
                    None, int(m.group(4)), int(m.group(5)),
                    int(m.group(6)) or 0
                ]

                if m.group(2):
                    opts['factor'] = ml[0]
                    ml[0] = None
                else:
                    ml[0] = float(m.group(1) or 1) / SAMPLING_RATE

                if m.group(3):
                    opts['func'] = _oscache[ m.group(3) ]
                    if not opts['func']: raise Exception(
                        "Oscillator not defined: {}".format(m.group(3))
                    )

                if m.group(7):
                    opts['env'] = Shape.from_string( "1:0;" + m.group(7) )

                attr_dir[i] = Modulation(*ml, **opts)
    
        attr_dir['amplitude_modulation'] = attr_dir.pop('AM')
        attr_dir['frequency_modulation'] = attr_dir.pop('FM')

        if attr_dir["W"]:
            attr_dir["wave_shape"] = Shape.from_string( attr_dir.pop("W") )

        oscillator = Oscillator(**attr_dir)

        if share:
            return (nfactor, deviation, share, envelope), oscillator
        else:
            return head, oscillator

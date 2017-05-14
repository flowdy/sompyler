# -*- coding: utf-8 -*-

from __future__ import division
from math import sqrt
from cpython cimport array
import array
import re
import copy
from operator import itemgetter

class Shape(object):

    def __init__(self, span, *coords):

        self.length = span[0]

        # scale x to tune length, y to 1
        x_max = coords[-1][0]
        y_max = span[1] or max( i[1] for i in coords )

        self.coords = [ (0, 1 if span[1] else 0 ) ]
        x_last = 0

        for i in coords:
            if x_last > i[0]:
                raise Exception(
                    "Wrong order in coordinates: {} not {} in {}".format(
                        x_last, i[0], coords
                    )
                )
    
            x_last = i[0]
    
            x = i[0] / x_max
    
            if i[1] < 0:
                raise Exception("y must not be less than 0")
            
            self.coords.append( ( x, i[1] / y_max ) )

    def iterate_coords(self, offset=0):
        it = iter(self.coords)
        length = self.length
        for i in range(offset): next(it)
        for i in it: yield (i[0] * length, i[1])

    def y_slice (self, offset, until, step):
        s = slice(offset, until, step)
        return tuple( c[1] for c in self.coords[s] )

    @classmethod
    def from_string(cls, bezier):
        """
        Shape.from_string("length:[y0;]x1,y1;x2,y2;...")

        Define the attack, sustain or release shape of the envelope as a bezier
        curve, that is, the coordinates of its outer polygon.

        length - the duration of the part of the envelope, in seconds
        y0 - the y value of point at x=0. Default is 0.
        """

        if ':' in bezier:
            coords, bezier = bezier.split(":",1)
            coords = [[ float(coords), 0 ]] # list with 1 item
        else:
            coords = [[ 1, 0 ]]

        m = re.match("(\d+);", bezier)
        coords[0][1] = int(m.group(1)) if m else 0

        if m:
            _, bezier = bezier.split(";",1)

        for m in bezier.split(";"):
            coords.append([ int(n) for n in m.split(",", 1) ])

        return cls(*coords)
    
    def render (self, unit_length=1, y_scale=1, adj_length=False ):
        "Get samples according to the bezier curve"

        coords = copy.deepcopy(self.coords)

        cdef int length

        if adj_length and isinstance(adj_length, bool):
            unit_length *= y_scale
            coords = self.new_coords(y_scale=y_scale) 
            length = int( unit_length * self.length + .5 )
        else:
            length = adj_length or self.length
            coords = self.new_coords(adj_length, y_scale)
            length = int( unit_length * length + .5 )

        if not length: return []

        approx = Shape._get_bezier_func(*coords)
    
        cdef float[:] results = array.array('f', [None]*(length+1))
        results[0] = coords[0][1]
        results[-1] = coords[-1][1]
    
        scan_bezier( approx, length, results, 0, .5, length )
    
        res = [x for x in results]
        return res

    def new_coords(self, adj_length=None, y_scale=None):
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

        if y_scale is None:
            y_scale = 1

        coords = copy.deepcopy(self.coords)

        if adj_length:
            if adj_length < 0:
                raise Exception("Negative shape length")
            adj_length /= self.length 
        elif y_scale == 1:
            return coords

        if adj_length > 1:
            pult_x = coords[-2][0]
            pult_y, ult_y = (i[1] for i in coords[-2:])
            ult_rise = (ult_y - pult_y) / (1 - pult_x)
            fill_x = adj_length
            fill_y = ult_y + (fill_x - 1) * ult_rise
            fill_x2 = None
            if fill_y < 0:
                # even out fall into negative to being constant 0
                fill_x2 = fill_x
                fill_x = -ult_y / ult_rise + 1
                fill_y = 0
            del coords[-1]
            coords.append(( fill_x, fill_y ))
            if fill_x2: coords.append([ fill_x2, fill_y])

        elif adj_length and adj_length < 1:
            n = 0
            for i in coords:
                if adj_length >= i[0]:
                   n += 1
                else: break
            h = coords[n-1]
            ult_rise = (i[1] - h[1]) / (i[0] - h[0])
            new_coord = ( adj_length,
                h[1] + (adj_length - h[0]) * ult_rise if i[1] else 0
            )
            del coords[n:]
            coords.append(new_coord)
    
        # rescale x-dimension to new maximum, y-dimension to y_scale
        x_max = max(c[0] for c in coords)
        return [ (c[0] / x_max, c[1] * y_scale) for c in coords ]

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

        assert len(lcoords) == len(rcoords)

        coords = []
        for i in range( len(lcoords) ):
            coords.append((
                avg( lcoords[i][0], rcoords[i][0] ),
                avg( lcoords[i][1], rcoords[i][1] )
            ))

        coords[0] = ( adj_length, coords[0][1] )

        return Shape(*coords)

    def edgy (self):
        return (self.coords[0][1], self.coords[-1][1])

    _b_cache = {}
    @staticmethod
    def _get_bezier_func(*coords):
    
        def b(n,k):
    
            v = Shape._b_cache.get( (n,k) )
            if v: return v
    
            if k == 0: v = 1
    
            elif 2*k > n:
                v = b(n,n-k)
    
            else:
                v = (n+1-k) / k * b(n,k-1)
    
            Shape._b_cache[ (n,k) ] = v
            return v
    
        def B(x,n,k): return lambda t: b(n,k) * x * t**k * (1-t)**(n-k)
    
        xf, yf, cnum = [], [], len(coords)-1
        for i, c in enumerate(coords):
            xf.append( B(c[0], cnum, i) )
            yf.append( B(c[1], cnum, i) )
    
        func = lambda t: (
            sum( f(t) for f in xf ),
            sum( f(t) for f in yf )
        )

        return func
    
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
        self.coords = Shape._adjust_coords_num( self.coords, num )

    @staticmethod
    def _adjust_coords_num (coords, num):
        if num > len(coords):
            return Shape._raise_coords( coords, num - len(coords) )
        elif num < len(coords):
            return Shape._lessen_coords( coords, len(coords) - num )
        else:
            return coords

    def lessen_coords (self, by_num):
        self.coords = Shape._lessen_coords( self.coords, by_num)

    @staticmethod
    def _lessen_coords (coords, by_num):
    
        def distance_c_to_ab(a, b, c):
            n_ab = (b[1] - a[1]) / (b[0] - a[0])
            if b[1] - a[1]:
                # print "a: {},{}; b: {},{}; c: {},{}".format(a[0], a[1], b[0], b[1], c[0], c[1])
                n_dc = (a[0] - b[0]) / (b[1] - a[1])
                x = (c[1] - n_dc*c[0] - b[1] + n_ab*b[0]) / (n_ab - n_dc)
            else: # work around division by zero
                x = c[0]
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
        self.coords = Shape._raise_coords( self.coords, by_num)

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
                x = coords[i][0] + (step+1) * interval
                y = (c[1] - coords[i][1]) / xlen * (x - c[0]) + c[1]
                new_coords.append( (x, y) )
    
            new_coords.append(c)
    
        assert sum_coords == by_num
    
        return new_coords
    
cdef void scan_bezier(
       object approx, int length, float[:] results,
       float start, float pos, int max
    ) except *:

    cdef float t = start + pos
    cdef float x, y
    x, y = approx( t );
    cdef int ix = int(x * length)
    results[ ix ] = y
    cdef float half_pos = pos / 2

    if results[ ix-1 ] is None:
        scan_bezier( approx, length, results, start, half_pos, ix-1 )
    elif x == length or results[ ix+1 ] is not None:
        return

    if x < max:
        scan_bezier( approx, length, results, start+pos, half_pos, max )

    return



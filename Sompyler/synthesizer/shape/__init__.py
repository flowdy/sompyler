# -*- coding: utf-8 -*-

from __future__ import division
from Sompyler.synthesizer.shape.bezier_gradient import plot_bezier_gradient
from Sompyler.synthesizer.shape.point import Point, Point2D, Point3D
import re
import copy
from operator import itemgetter

class Shape(object):
    __slots__ = ['length', 'coords', 'y_max']
    def __init__(self, span, *coords):

        self.length = span[0]

        if not next(i for i in coords if not isinstance(i, Point)):
            self.coords = coords
            return

        # scale x to tune length, y to 1
        x_max = coords[-1][0]
        y_max = span[1] or max( i[1] for i in coords )

        self.coords = [ Point2D(0, 1 if span[1] else 0) ]
        self.y_max = y_max
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

            self.coords.append(
                Point2D( x, i[1] / y_max ) if len(i) == 2
                    else Point3D( x, i[1] / y_max, i[2] )
            )

    def iterate_coords(self, offset=0):
        it = iter(self.coords)
        length = self.length
        for i in range(offset): next(it)
        for i in it:
            if isinstance(i, Point3D):
                props = { "frequency": i.x * length, "max_volume": i.y, "envelope": i.env }
            else:
                props = { "position": i.x * length, "volume": i.y }
            yield i

    def y_slice (self, offset, until, step):
        s = slice(offset, until, step)
        return tuple( c.y for c in self.coords[s] )

    def rescale_y (self, other_y_max):
        adj_y = self.y_max / other_y_max
        for i in self.coords:
            i.y *= adj_y
        self.y_max = other_y_max

    @classmethod
    def from_string(cls, bezier):
        """
        Shape.from_string("length:[y0;]x1,y1;x2,y2;...")

        Define the attack, sustain or release shape of the envelope as a bezier
        curve, that is, the coordinates of its outer polygon.

        Attributes:
          * length - the duration of the part of the envelope, in seconds
          * y0 - the y value of point at x=0. Default is 0.
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

    def render (self, unit_length=1, y_scale=1, adj_length=False, final_boost=None ):
        "Get samples according to the bezier curve"

        if adj_length and isinstance(adj_length, bool):
            unit_length *= y_scale
            coords = self.new_coords(y_scale=y_scale) 
            length = int( unit_length * self.length + .5 )
        else:
            length = adj_length or self.length
            coords = self.new_coords(adj_length, y_scale)
            length = int( unit_length * length + .5 )

        if not length: return []

        if final_boost and (float(final_boost.y_max) / self.y_max) > coords[-1].y:
            Shape.add_final_boost( final_boost, coords, length )

        return plot_bezier_gradient( length, *coords )

    def new_coords(self, adj_length=None, y_scale=1, reverse=False):
        """
        Return new, independent coordinate points that span original length
        or a specified one.

        If specified length is less than the original, coordinates are ignored
        from the end. The last is adjusted linearly.

        If specified length is more than original, coordinates are added at
        the tail, linearly advancing in the direction defined last. When
        it hits the y-axis, it proceeds in horizontal direction, because
        negative values are not allowed.
        """

        if adj_length:
            if adj_length < 0:
                raise Exception("Negative shape length")
            adj_length /= self.length 
        elif y_scale == 1:
            coords = self.coords
            if reverse: return reversed(coords)
            else: return coords

        coords = self.coords[:]

        if adj_length > 1:
            pult_x = coords[-2].x
            pult_y, ult_y = (i.y for i in coords[-2:])
            ult_rise = (ult_y - pult_y) / (1 - pult_x)
            fill_x = adj_length
            fill_y = ult_y + (fill_x - 1) * ult_rise
            fill_x2 = None
            if fill_y < 0:
                # even out fall into negative to being constant 0
                fill_x2 = fill_x
                fill_x = -ult_y / ult_rise + 1
                fill_y = 0
            replaced = coords.pop(-1)
            coords.append(replaced.new_alike( fill_x, fill_y ))
            if fill_x2: coords.append(
                replaced.new_alike( fill_x2, fill_y )
            )

        elif adj_length and adj_length < 1:
            n = 0
            for i in coords:
                if adj_length >= i.x:
                   n += 1
                else: break
            h = coords[n-1]
            new_coord = Point.weighted_average(
                h, (adj_length - h.x) / (i.x - h.x), i
            )
            del coords[n:]
            coords.append(new_coord)

        # rescale x-dimension to new maximum, y-dimension to y_scale
        x_max = coords[-1].x
        return [ c.new_alike(c.x / x_max, c.y * y_scale) for c in coords ]

    @staticmethod
    def add_final_boost( boost_shape, coords, length ):

        boost_x_offset = length - boost_shape.length

        if boost_x_offset < 0: # we cut boost short from the front
           boost_coords = boost_shape.new_coords(length, reverse=True)
           boost_shape = Shape(
               (length, 0), *reversed(boost_coords)
           )
           boost_x_offset = 0

        def line_segment_progressor(shape, x_offset=None):
            old = ( coords[0] if x_offset is None
                    else coords[0].new_alike( coords[0].x + x_offset )
                  )
            for i in coords[1:]:
                if x_offset:
                    i = i.new_alike(i.x + x_offset)
                yield (old, i)
                old = i
                offset = offset + 1

        progress_self  = line_segment_progressor(self)
        progress_boost = line_segment_progressor(boost_shape, boost_x_offset)

        is_flags = 0
        take_sustain = []
        while not is_flags == 3:

            if not is_flags & 2:
                s_begin, s_end = progress_sustain()
                take_sustain.append(s_begin)
            if not is_flags & 1:
                b_begin, b_end = progress_boost()

            is_flags = 0 # intersection
            if s_end.x >= b_end_x: is_flags = is_flags | 2
            if s_end.y >= b_end.y: is_flags = is_flags | 1

        x = ( b_begin.y - s_begin.y ) / (
                ( s_end.y - s_begin.y ) / ( s_end.x - s_begin.x )
              - ( b_end.y - b_begin.y ) / ( b_end_x - b_begin_x )
            )
        s_intersect = Point.weighted_average(
            s_begin, (x - s_begin.x) / (s_end.x - s_begin.x), s_end
        )
        take_sustain.append(s_intersect)
        take_sustain.append(b_end)
        for i in progress_boost:
            p = i[1].new_alike( i[1].x + boost_x_offset )
            take_sustain.append(p)

        return take_sustain

    @classmethod
    def weighted_average (cls, left, dist, right):
        """
        Assuming a smooth transition to a right curve in a distance,
        Shape.weighted_average(left_shape, distance, right_shape) returns an
        intermediate shape at a given position < 1 and > 0.
        """

        assert not ( dist < 0 or dist > 1 )

        def avg(a, b): return (1 - dist) * a + dist * b

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
            coords.append(Point.weighted_average( lcoords[i], dist, rcoords[i] ))

        return Shape( (adj_length, coords[0].y), *coords )

    def edgy (self):
        return (self.coords[0].y, self.coords[-1].y)

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
            n_ab = (b.y - a.y) / (b.x - a.x)
            if n_ab:
                n_dc = (a.x - b.x) / (b.y - a.y)
                x = (c.y - n_dc*c.x - b.y + n_ab*b.x) / (n_ab - n_dc)
            else: # work around division by zero
                x = c.x
            return Point.distance( Point(x, n_ab*(x - b.x) + b.y), c )

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
            distances[c] = Point.distance(c_last, c)
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

            xlen = c.x - coords[i].x
            interval = xlen / (inter_coords + 1)

            for step in range(inter_coords):
                x = coords[i].x + (step+1) * interval
                y = (c.y - coords[i].y) / xlen * (x - c.x) + c.y
                new_coords.append( Point2D(x, y) )

            new_coords.append(c)

        assert sum_coords == by_num

        return new_coords


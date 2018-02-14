# -*- coding: utf-8 -*-
from .sympartial import Sympartial, Oscillator, log_to_linear
from .envelope import Envelope, Shape
from .shape.point import SympartialPoint
import numpy as np
import re
from itertools import repeat, chain

def _deviate(f, d):
    return f * 2 ** (d/1200)

class SoundGenerator(Shape):
    __slots__ = ('spread')

    @classmethod
    def shape(cls, initial, the_list, term, spread):
        """ Get a new SoundGenerator instance. Please note:
            This function is not called __init__() just because
            we later need to call __init__ explicitly from
            the parent, but with us as the actual invocant.
        """

        partial_seqno = 0
        cum_deviation = 0
        def spreaditer():
            nonlocal partial_seqno, cum_deviation
            for dev in chain(spread, repeat(0)):
                partial_seqno += 1
                cum_deviation += int(dev)
                yield _deviate(partial_seqno, cum_deviation)

        sprit = spreaditer()

        if initial is None:
            try:
                initial = next(p[2] for p in the_list if p[2] is not None)
            except StopIteration as e:
                raise RuntimeError(
                    "No sympartial found for sound_generator from "
                  + repr(the_list)
                )
        mylist = [(0.0, 0, initial)]

        for p in the_list:
            p = (_deviate(next(sprit), p[0]), p[1], p[2])
            mylist.append(p)
    
        if term is None:
            term = next(p[2] for p in reversed(the_list) if p[2] is not None)
    
        mylist.append(( int(mylist[-1][0])+1.0, 0, term ))
    
        last_freq = 0
        last_symp = None
    
        tmp = []
    
        for i1, v in enumerate(mylist):
    
            if len(v) == 2:
                freq0, volume = v
                symp = None
            else:
                freq0, volume, symp = v

            if symp is None:
                tmp.append(i1)
                continue

            for tv in tmp:
                freq = mylist[tv][0]
                volume = mylist[tv][1]
                left = freq - last_freq
                right = freq0 - freq
                dist = left / (left + right)
                mylist[tv] = (
                    freq, volume,
                    Sympartial.weighted_average(last_symp, dist, symp)
                )
    
            tmp = []
            last_freq = freq0
            last_symp = symp
    
        soundgen = cls( (mylist[-2][0], 0), *mylist[1:-1] )
        soundgen.spread = sprit
        del soundgen.coords[0]

        return soundgen

    def render(self, base_freq, duration=0, args=None):

        if args is None: args = {}
        elif not isinstance(args, dict):
             raise Exception(
                 "further arg(s) have wrong type: {}".format(
                 type(args)
             ))
        samples = np.array([0.0])
        sympit = self.iterate_coords()
        total_share = 0

        for s in sympit:
            sympres = s.symp.render(
                base_freq * s.x, s.y, duration, args
            )
            len1 = len(samples)
            len2 = len(sympres)
            if len1 > len2:
                sympres = np.append( sympres, np.zeros(len1-len2) )
            elif len2 > len1:
                samples = np.append( samples, np.zeros(len2-len1) )
            samples = samples + sympres
            
        return samples


    @classmethod
    def weighted_average(cls, l, dist, r):

        if l.length != r.length:
            shorter, longer = sorted((l, r), key=lambda s: s.length )
            div = longer.length / shorter.length
            while shorter.coords[-1].x < div:
                x = next(shorter.spread)
                overflowing_x = x / shorter.length
                shorter.coords.append(
                    longer.coords[-1].new_alike(x=overflowing_x, y=0)
                )
            for c in shorter.coords: c.x /= div
            shorter.length = x

        self = super().weighted_average(l, dist, r, coord0=False)
        del self.coords[0]

        return self

    @classmethod
    def _raise_coords(cls, coords, by_num):
        """ Insert coordinates with y=0 between those with the greatest
            distance to each other. The new coordinates, and the neighbours
            are equally distant.
        """

        distances = {}
        c_last = coords[0]

        new_coords = [c_last]

        for c in coords[1:]:
            distances[c] = c.x - c_last.x
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

            for step in range(inter_coords):
                dist = (step+1) / (inter_coords+1) * 1
                x = (1 - dist) * coords[i].x + dist * c.x
                s = c.symp.weighted_average( coords[i].symp, dist, c.symp )
                new_coords.append( SympartialPoint(x, 0, s) )

            new_coords.append(c)

        assert sum_coords == by_num

        return new_coords

    @classmethod
    def _lessen_coords (cls, coords, by_num):
        """ The greater the value on the x-axis, the less its difference to
            x of the previous coordinate and the less also the amplitude (y),
            the more likely is that a coordinate gets dropped.
        """

        distances = {}

        for i, c in enumerate(coords[1:]):
            distances[c] = ( (c.x - coords[i].x) * c.y / c.x, coords[i] )

        sorted_distance_to_prev = [
                (c, d[1]) for c, d in sorted(
                    distances.items(), key=lambda i: i[1][0]
                )
            ]

        new_coords = []
        for c, prev in sorted_distances_to_prev[0:by_num]:
            dist = 1.0 * ( c.y / (prev.y or c.y) )
            new_coords.append(
                c.weighted_average( prev, dist, c )
            )
            if c in distances:
                distances.drop(c)
            if prev in distances:
                distances.drop(prev)

        new_coords.extend( c for c in distances )
        new_coords.sort(lambda c: c.x)
        return new_coords



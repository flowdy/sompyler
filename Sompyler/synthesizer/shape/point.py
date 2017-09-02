from __future__ import division
from math import sqrt

class Point(object):
    __slots__ = ['x', 'y']
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @staticmethod
    def distance (a, b):
        return sqrt( (b.y - a.y)**2 + (b.x - a.x)**2 )

    @staticmethod
    def _weighted_average(a, dist, b):
        x = (1 - dist) * a.x + dist * b.x
        y = (1 - dist) * a.y + dist * b.y
        return (x, y)

    @classmethod
    def weighted_average(cls, *args):
        return cls(*Point._weighted_average(*args))

    def new_alike(self, x=None, y=None, *further):
        if x is None:
            x = self.x
        if y is None:
            y = self.y
        return self.__class__(x, y, *further)

    def __getitem__(self, n):
        if n > 1: return IndexError
        return self.y if n else self.x

    def __len__(self): return 2

class BezierEdgePoint(Point):
    __slots__ = ['is_sharp']
    def __init__(self, x, y, is_sharp):
        if is_sharp is None:
            raise AttributeError("Missing is_sharp boolean flag")
        super(BezierEdgePoint, self).__init__(x, y)
        self.is_sharp = is_sharp

    def new_alike(self, x=None, y=None, is_sharp=None):
        if is_sharp is None:
            is_sharp = self.is_sharp
        return super(BezierEdgePoint, self).new_alike(x, y, is_sharp)

    def __getitem__(self, n):
        return self.is_sharp if n == 2 else Point.__getitem__(self, n)

    def __len__(self): return 3

    @classmethod
    def weighted_average(cls, a, dist, b):
        if not isinstance(b, BezierEdgePoint):
            raise TypeError("Points are not compatible")
        x, y = super(BezierEdgePoint, cls)._weighted_average(a, dist, b)
        if a.is_sharp == b.is_sharp:
            is_sharp = a.is_sharp
        elif a.is_sharp:
            is_sharp = dist
        elif b.is_sharp:
            is_sharp = 1 - dist
        else:
            raise RuntimeError("Impossible else entered")
        return cls(x, y, is_sharp)

class SympartialPoint(Point):
    __slots__ = ['symp']
    def __init__(self, x, y, symp):
        if symp is None:
            raise AttributeError("Missing a sympartial for SympartialPoint instance")
        super(SympartialPoint, self).__init__(x, y)
        self.symp = symp

    def new_alike(self, x=None, y=None, symp=None):
        if symp is None:
            symp = self.symp
        return super(SympartialPoint, self).new_alike(x, y, symp)

    def __getitem__(self, n):
        return self.symp if n == 2 else Point.__getitem__(self, n)

    def __len__(self): return 3

    @classmethod
    def weighted_average(cls, a, dist, b):
        if not isinstance(b, BezierEdgePoint):
            raise TypeError("Points are not compatible")
        x, y = super(SympartialPoint, cls)._weighted_average(a, dist, b)
        if a.is_sharp == b.is_sharp:
            is_sharp = a.is_sharp
        elif a.is_sharp:
            is_sharp = dist
        elif b.is_sharp:
            is_sharp = 1 - dist
        else:
            raise RuntimeError("Impossible else entered")
        return cls(x, y, is_sharp)


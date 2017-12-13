class Stressor:

    __slots__ = ('_tuple', '_next', '_cumlen', '_all_maxv')

    def __init__(self, strings):

        steps = []

        for step in strings[0].split(','):

            if '-' in step:
               minv, maxv = step.split('-', 1)
            else:
               maxv = step
               minv = 0

            steps.append( ( int(minv), int(maxv)) )

        self._tuple = tuple(steps)
        if len(strings) > 1:
            self._next = Stressor(strings[1:])
            self._cumlen = self._next.cumlen
        else:
            self._next = None
            self._cumlen = 1
        self._all_maxv = max( i[1] for i in self._tuple )

    @property
    def cumlen(self): return len(self._tuple) * self._cumlen

    def of(self, pos, all):
        int_pos = int( pos / self._cumlen )
        remainder = pos % self._cumlen
        if int_pos * self._cumlen not in all:
            exponent = self._tuple[ int_pos ][1]
            all.add( int_pos * self._cumlen )
        else:
            if self._next:
                exponent = self._next.of(remainder, all)
            else:
                exponent = 1
            minv, maxv = self._tuple[ int_pos ]
            exponent *= (maxv - minv) * exponent + minv

        return exponent / self._all_maxv


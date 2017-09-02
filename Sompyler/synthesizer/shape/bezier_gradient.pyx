# -*- coding: utf-8 -*-

from cpython cimport array
import array

cdef double NOT_INITIALIZED = float(0xDEADBEEF)

def plot_bezier_gradient( length, *coords ):

    approx = get_bezier_func(*coords)

    cdef double[:] results = array.array( 'd', [NOT_INITIALIZED]*length )
    results[0] = coords[0].y
    results[-1] = coords[-1].y

    scan_bezier( approx, length-1, results, 0, .5, length-1 )

    return [x for x in results]

cdef void scan_bezier(
       object approx, int length, double[:] results,
       double start, double pos, int max
    ) except *:

    cdef double t = start + pos
    cdef double x, y
    x, y = approx( t );
    cdef int ix = int(x * length)
    results[ ix ] = y
    cdef double half_pos = pos / 2

    if results[ ix-1 ] == NOT_INITIALIZED:
        scan_bezier( approx, length, results, start, half_pos, ix-1 )
    elif length and results[ ix+1 ] != NOT_INITIALIZED:
        return

    if ix < max:
        scan_bezier( approx, length, results, start+pos, half_pos, max )

    return

_b_cache = {}
def b(n,k):

    v = _b_cache.get( (n,k) )
    if v: return v

    if k == 0: v = 1

    elif 2*k > n:
        v = b(n,n-k)

    else:
        v = (n+1-k) / k * b(n,k-1)

    _b_cache[ (n,k) ] = v
    return v

def get_bezier_func(*coords):

    x0 = coords[0].x
    max = coords[-1].x - x0

    len_coords = len(coords) - 1
    cdef double[:] xb = array.array('d', [
        (c.x - x0) / max * b(len_coords, i) for i, c in enumerate(coords)
    ])
    cdef double[:] yb = array.array('d', [
        c.y * b(len_coords, i) for i, c in enumerate(coords)
    ])

    return lambda t: (sum_polynom(xb, t), sum_polynom(yb, t))
    
cdef double sum_polynom(double[:] cb, double t):

     # b(n,k) * x * t**k * (1-t)**(n-k)

     cdef double res = 0.0

     cdef int n = len(cb)-1
     cdef int k
     for k in range(n+1):
         res += cb[k] * t**k * (1-t)**(n-k)

     return res

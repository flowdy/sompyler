def plot_bezier_gradient( length, *coords ):

    approx = get_bezier_func(*coords)
    
    results = [None]*length
    results[0] = coords[0].y
    results[-1] = coords[-1].y
    
    scan_bezier( approx, length-1, results, 0, .5, length-1 )
    
    return results

def scan_bezier(approx, length, results, start, pos, max):

    t = start + pos
    x, y = approx( t ); x = int(x * length)
    results[ x ] = y
    half_pos = pos / 2

    if results[ x-1 ] is None:
        scan_bezier( approx, length, results, start, half_pos, x-1 )
    elif results[ x+1 ] is not None:
        return

    if x < max:
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

    len_coords = len(coords) - 1
    xb = [
        c.x * b(len_coords, i) for i, c in enumerate(coords)
    ]
    yb = [
        c.y * b(len_coords, i) for i, c in enumerate(coords)
    ]

    return lambda t: (sum_polynom(xb, t), sum_polynom(yb, t))
    
def sum_polynom(cb, t):

     res = 0.0

     n = len(cb)-1
     for k, b in enumerate(cb):
         res += b * t**k * (1-t)**(n-k)

     return res

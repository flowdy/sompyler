stimm = [3, 0, 11.73, 3.91, 15.64, -13.69, -1.96, -9.78, 1.96, 13.69, -15.64, -3.91, -11.73]
offset = stimm[0]
tunes = [i*100+c for i, c in enumerate(stimm[1:])]
tune0 = tunes[ -offset % 12 ]
def freq(n, stimm):
    # tunes = [ (c - tunes[ -offset % 12 ]) % 1200 for c in tunes ]
    i = (n - offset - 1) % 12
    cent = int( (n-49) / 12 ) * 1200 + (tunes[i] - tune0) % 1200
    return 440 * 2 ** ( cent/1200.0 )

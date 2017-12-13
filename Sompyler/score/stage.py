import re

class Stage:

    def __init__( self, space, voices, tuner ):

        m = re.match(r'(\d+):(\d+)\|(\d+):(\d+)', space)
        if m:
            space = {
                'varvol': int( m.group(1) ),
                'basevol': int( m.group(2) ),
                'vardir': float( m.group(3) ),
                'framedir': float( m.group(4) ),
            }
        else:
            raise SyntaxError("room_spread: VARVOL:BASE_VOL|VARDIR:FRAMEDIR")
        
        sum_intensities = 0

        self.voices = {}

        for name, ch_data in voices.items():
            if isinstance(ch_data, str):
                 direction, distance, instrument = ch_data.split()
                 tuning = tuner()
            else:
                 direction, distance, instrument, tuning = (
                     ch_data.pop(i, None) for i in (
                         'direction', 'distance', 'instrument', 'tuning'
                     )
                 )
                 tuning = tuner(tuning)
                 
            voice = self.voices[ name ] = Voice(
                space, direction, float(distance), instrument, tuning
            )

            sum_intensities += voice.intensity

        for voice in self.voices.values():
            i = voice.intensity / sum_intensities
            left, right = voice.position
            voice.position = ( left*i, right*i )


class Voice:
    __slots__ = ('tuning', 'instrument', 'position', 'intensity')

    def __init__(self, space, direction, distance, instrument, tuning):

        self.tuning     = tuning
        self.instrument = instrument

        varvol = space['varvol']
        basevol = space['basevol']
        vardir = space['vardir']
        framedir = space['framedir']

        if distance > varvol:
            raise ValueError("distance cannot be greater than varvol")
        
        self.intensity = basevol + varvol - distance

        m = re.match(r'(\d+)\|(\d+)', direction)
        if m:
            left = float(m.group(1))
            right = float(m.group(2))
            both = left + right
        else:
            raise SyntaxError("direction: 0-100|0-100")
        
        left  = (framedir + left/both*vardir ) / (framedir + vardir)
        right = (framedir + right/both*vardir) / (framedir + vardir)
        max_ampl = max(left, right)

        self.position = (left / max_ampl, right / max_ampl)

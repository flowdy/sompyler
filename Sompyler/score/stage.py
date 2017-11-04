import re

class Stage(object):

    def __init__( self, space, voices, tuner ):

        m = re.match(r'(\d+):(\d+)|(\d+):(\d+)', space)
        if m:
            space = {
                'varvol': float( m.group(1) ),
                'basevol': float( m.group(2) ),
                'vardir': float( m.group(3) ),
                'framedir': float( m.group(4) ),
            }
            space['spread'] = vardir / (vardir + framedir or 1)
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
                 
            self.voices[ name ] = Voice(
                space, direction, distance, instrument, tuning
            )

            sum_intensities += voice.intensity

        for voice in self.voices.items():
            i = voice.intensity / sum_intensities * 1.0
            left, right = voice.position
            voice.position = ( left/i, right/i )


class Voice(object):
    __slots__ = ('tuning', 'instrument', 'position')

    def __init__(self, space, direction, distance, instrument, tuning):

        self.tuning     = tuning
        self.instrument = instrument

        if distance > space['varvol']:
            raise ValueError("distance cannot be greater than varvol")
        
        self.intensity = (space['basevol'] + distance) 

        m = re.match(r'(\d+)([RL])(\d+)', direction)
        if m:
            more = float(m.group(1))
            direction = m.group(2)
            less = float(m.group(3))
        else:
            raise SyntaxError("direction: 0-100[RL]0-100")
        
        dir = more / ( more + less or 1 )
        right = 1 + dir * space['spread'] * (1 if direction == 'R' else -1 )
        left  = 1 + dir * space['spread'] * (1 if direction == 'L' else -1 )
        max_ampl = max(left, right)

        self.position = (left / max_ampl, right / max_ampl)





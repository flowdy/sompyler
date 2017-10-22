import re

class Channel(object):
    __slots__ = ('tuning', 'instrument', 'position')

    sum_intensities = 0

    def __init__(self, room, direction, distance, instrument, tuning=None):

        self.tuning     = tuning
        self.instrument = instrument

        m = re.match(r'(\d+)\|(\d+);(\d+)\|(\d+)', room)
        if m:
            varvol  = float( m.group(1) )
            basevol = float( m.group(2) )
            vardir = float( m.group(3) )
            framedir = float( m.group(4) )
            spread = vardir / (vardir + framedir)
        else:
            raise SyntaxError("room_spread: VARVOL|BASE_VOL;VARDIR|FRAMEDIR")
        
        if distance > varvol:
            raise ValueError("vardist cannot be greater than varvol")
        
        self.intensity = (basevol + distance) 
        Channel.sum_intensities += self.intensity

        m = re.match(r'(\d+)([RL])(\d+)', direction)
        if m:
            more = float(m.group(1))
            direction = m.group(2)
            less = float(m.group(3))
        else:
            raise SyntaxError("direction: 0-100[RL]0-100")
        
        dir = more / ( more + less )
        right = 1 + (dir*spread) * (1 if direction == 'R' else -1 )
        left  = 1 + (dir*spread) * (1 if direction == 'L' else -1 )
        max_ampl = max(left, right)
        right /= max_ampl
        left  /= max_ampl

        channel.position = (left, right)

    def set_amplitudes(self):

        if not hasattr(self, 'position'):
            i = self.intensity / Channel.sum_intensities * 1.0
            left, right = channel.raw_position
            self.position = ( left/i, right/i )
        
        return self.position



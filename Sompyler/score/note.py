import re

class Note:
    """ Abstract description of a tone

    Mandatory properties: pitch in Hz, length in seconds, stress

    Optional properties:
      * occurrences in the score, expected as tuple of three values:
        * position in the time line, in seconds
        * volume on the left channel, on the range 0.0 (mute) to 1.0 (max. vol)
        * volume on the right channel, on the range 0.0 (mute) to 1.0 (max. vol)
        (First or only occurrence can be given as "occurrence" parameter to
        the constructor, but any further need to be passed by
        note.add_occurrence(time_pos, left_pos, right_pos).)
      * num_samples, if known or tone has been calculated
      * 'am_shape', 'fm_shape' and other, instrument-specific properties

    """

    __slots__ = (
        'instrument', 'stress', 'pitch', 'properties', 'length_ticks',
        'length_secs', 'num_samples', '_occurrences'
    )

    def __init__(
            self, instrument, pitch, length, stress,
            occurrence=None, num_samples=None, **properties
        ):

        self.instrument = instrument
        self.pitch = pitch
        self.length_ticks = length # need to be converted to seconds at upper
        self.length_secs = 0       # level as tempo_shape must be respected.
        self.stress = stress
        self.properties = properties
        self._occurrences = []

        if occurrence is not None:
            self.add_occurrence(*occurrence)

        if num_samples is not None:
            self.num_samples = num_samples

    @classmethod
    def from_score(
            cls, instrument, dynamic_stress, properties,
            offset_ticks, position, tuner
        ):

        if isinstance(properties, str):
            properties = properties.split(" ", 2)
            if len(properties) < 3:
                properties.append( 1 )
            pitch, length, weight = properties
            properties = { 'pitch': pitch, 'length': length, 'weight': weight }
         
        if 'pitch' not in properties:
           properties['pitch'] = properties.pop("P")
        if 'length' not in properties:
           properties['length'] = properties.pop("L")
        if 'weight' not in properties:
           properties['weight'] = properties.pop("W", 1)
        
        offset_ticks += properties.pop('offset', 0)
        length_ticks = float( properties.pop('length') )
        properties = properties

        weight = properties.pop('weight')
        if isinstance(weight, str):
            m = re.match(r'(\d+)(?:\*([\d.]+))?', weight)
            if m:
                stress = (
                    int( m.group(1) ),
                    dynamic_stress * float( m.group(2) or 1 )
                )
            else:
                raise SyntaxError(
                    "Weight must be integer or 'integer*float', "
                    "second representing extra stress_factor"
                )
        else:
            stress = (float(weight), dynamic_stress)

        m = re.match(
            r'(\S+?\d)([+-]\d+)?$', properties['pitch']
        )
        if m:
            pitch = tuner( m.group(1) ) * 2 ** (
                int( m.group(2) or 0 ) / 1200.0
            )
        else:
            raise SyntaxError(
                properties['pitch']
                + ": Could not recognize pitch of note, "
                + "optional deviation in cent"
            )

        del properties['pitch']

        return offset_ticks, (position, cls(
            instrument, pitch, length_ticks, stress,
            **properties
        ))

    @classmethod
    def from_csv(cls, instrument, pitch, length, stress, num_samples, *other):

        other = dict( o.split('=', 1) for o in other )
        other['num_samples'] = int(num_samples)
        note = cls(instrument, pitch, 0, stress, **other)
        note.length_secs = length
        return note

    def add_occurrence(self, time_position, left, right):

        time_position = float(time_position)
        left = float(left)
        right = float(right)

        self._occurrences.append( (time_position, (left, right)) )
        
    def add_occurrences_of(self, other):
        for time_pos, (left, right) in other._occurrences:
            self.add_occurrence(time_pos, left, right)

    def is_unused(self):
        return not self._occurrences

    def occurrence_iter(self):
        return (o for o in self._occurrences)

    def _sorted_properties_tuple(self):

        return tuple(
            sorted(
                (i for i in self.properties.items()),
                key=lambda i: i[0]
            )
        )

    def __hash__(self):

        relevant_data = (
                self.instrument,
                str(self.stress),
                str(self.pitch),
                str(self.length_secs)
            ) + self._sorted_properties_tuple()

        return hash(relevant_data)

    def __eq__(self, other):

        return (
           self.instrument == other.instrument
           and str(self.pitch)  == str(other.pitch)
           and str(self.stress) == str(other.stress)
           and str(self.length_secs) == str(other.length_secs)
           and self._sorted_properties_tuple()
            == other._sorted_properties_tuple()
        )

    def __str__(self):
        s = "Note played by {} at pitch {:0.3f} with stress {:4.3f}, {:3.2f}s long".format(
            self.instrument, self.pitch, self.stress, self.length_secs)
        if self.properties:
            s += " (Further properties: " + str(self.properties) + ")"
        return s
              
    def to_csvible_tuple(self): return (
            self.instrument, self.pitch, self.length_secs, self.stress
        ) + (self.num_samples,) + tuple(
            '{}={}'.format(*i) for i in self.properties.items()
        )


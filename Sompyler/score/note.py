class Note(object):
    __slots__ = (
        'instrument', 'stress', 'pitch',
        'properties', 'length', 'occurrences'
    )

    def __init__(
            self, instrument, stress, properties,
            calc_span, total_offset, offset_ticks, position, tuner
        ):

        if isinstance(properties, str):
            pitch, length, weight = str.split(" ", 2)
            properties = { 'pitch': pitch, 'length': length, 'weight': weight }
         
        if 'pitch' not in properties:
           properties['pitch'] = properties.pop["P"]
        if 'length' not in properties:
           properties['length'] = properties.pop("L")
        if 'weight' not in properties:
           properties['weight'] = properties.pop("W", 1)
        
        self.instrument = instrument
        offset_ticks += properties.get('offset', 0)
        offset, self.length = calc_span(
            offset_ticks, properties.pop('length')
        )
        offset += total_offset
        self.occurrences = [ (float(offset), position) ]
        self.properties = properties

        weight = properties.pop('weight')
        if isinstance(weight, str):
            m = rx.match(r'(\d+)*([\d.]+)', weight)
            if m:
                note.stress = (
                    int( m.group(1) ),
                    stress * float( m.group(2) )
                )
            else:
                raise SyntaxError(
                    "Weight must be integer or 'integer*float', "
                    "second representing extra stress_factor"
                )
        else:
            self.stress = (float(weight), stress)

        m = re.match(
            r'(\S+?\d)([+-]\d+)?$', properties['pitch']
        )
        if m:
            self.pitch = tuner( m.group(1) ) * 2 ** (
                int( m.group(2) or 0 ) / 1200.0
            )
        else:
            raise SyntaxError(
                properties['pitch']
                + ": Could not recognize pitch of note, "
                + "optional deviation in cent"
            )

        del properties['pitch']

        return
        
    def _sorted_properties_tuple(self):

        return tuple(
            sorted(
                (i for i in self.properties.items()),
                key=lambda i: i[0]
            )
        )

    def __hash__(self):

        relevant_data = (
                self.instrument, self.stress, self.pitch, self.length
            ) + self._sorted_properties_tuple()

        return hash(relevant_data)

    def __eq__(self, other):

        return (
           self.instrument == other.instrument
           and self.pitch  == other.pitch
           and self.stress == other.stress
           and self.length == other.length
           and self._sorted_properties_tuple()
            == other._sorted_properties_tuple()
        )

    def __str__(self):
        return ( "Note played by " + self.instrument
               + " at pitch " + note.pitch + "Hz"
               + " with stress " + note.stress
               + ", " + note.length + "s long"
               + " (Further properties: ", str(self.properties), ")"
               )
              

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
        self.occurrences = { float(offset): position }
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
                    "Weight is '" + weight
                  + ", expecting integer or integer*stress_factor"
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
                + ": Could not recognize consist of note and "
                + "optional deviation in cent"
            )

        return
        

    def hash_same_wherever_occurs(self):

        relevant_data = (
                self.instrument, self.stress, self.pitch, self.length
            ) + tuple(sorted(
                    (i for i in self.properties.items()),
                    key=lambda i: i[0]
                ))

        return hash(relevant_data)

    def __repr__(self):
        return ( "Note played by " + self.instrument
               + " at pitch " + note.pitch + "Hz"
               + " with stress " + note.stress
               + ", " + note.length + "s long"
               )
              

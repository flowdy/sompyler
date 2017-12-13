def first( attr, variants ):

    attr_checks = []
    for key in sorted( variants ):
        if attr is None and '=' in key:
           attrkey, attrval = key.split('=')
           attr_checks.append( (attrkey, attrval, variants[key]) )
        else:
           attr_checks.append( (key, variants[key]) )

    def _composer(note):

        for i in attr_checks:
            if len(i) == 2 and attr is None:
               if note.get(i[0]):
                   return i[1]
            elif attr is None:
               v = note.get(i[0])
               if v and v == i[1]:
                   return i[2]
            else:
               v = note.get(attr)
               if v and v == i[0]:
                   return i[1]

    def get_sound_generator(note):
        c = _composer(note)
        if c is None: return
        return c.sound_generator_for(note)

    return sound_generator_getter 

def stack( attr, variants ):

    attr_checks = []
    for key in sorted( variants ):
        if attr is None and '=' in key:
           attrkey, attrval = key.split('=')
           attr_checks.append( (attrkey, attrval, variants[key]) )
        else:
           attr_checks.append( (key, variants[key]) )

    def _composer(note):

        sound_generators = []
        for i in attr_checks:
            if len(i) == 2 and attr is None:
               if note.get(i[0]):
                   v = i[1]
            elif attr is None:
               v = note.get(i[0])
               if v and v == i[1]:
                   v = i[2]
            else:
               v = note.get(attr)
               if v and v == i[0]:
                   v = i[1]
               else: continue
            sound_generators.append(v.sound_generator_for(note))

        if len(sound_generators) > 1:
            last_sg = sound_generators[0]
            for sg in sound_generators[1:]:
                last_sg = last_sg.derive( sg )
            return last_sg
        elif sound_generators:
            return sound_generators[0]
        else: return

    return _composer

def merge( attr, variants ):

    attr_checks = []
    for key in sorted( variants ):
        attr_checks.append( (key, variants[key]) )

    def _composer(note):

        attrval = note.get(attr)
        if attrval is None:
            return

        leftv = None
        lastval = None
        for v in attr_checks:

            if attrval == v[0]:
                return v[1].sound_generator_for(note)
            elif attrval < v[0]:
                if leftv is None:
                    return v[1].sound_generator_for(note)
                else:
                    dist = (attrval - lastval) / (v[0] - lastval)
                    left_sg = leftv.sound_generator_for(note)
                    right_sg = v[1].sound_generator_for(note)
                    return left_sg.weighted_average( left_sg, dist, right_sg )
            else:
                lastval, leftv = v

        raise Exception("No sound generator matching for that note")

        return leftv.sound_generator_for(note)

    return _composer


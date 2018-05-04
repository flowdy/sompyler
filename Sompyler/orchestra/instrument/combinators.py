class Combinator:
    
    def __init__( attr, variants ):

        attr_checks = []
        for key in sorted( variants ):
            if attr is None and '=' in key:
               attrkey, attrval = key.split('=')
               attr_checks.append( (attrkey, attrval, variants[key]) )
            else:
               attr_checks.append( (key, variants[key]) )

        self.attr_checks = attr_checks
        self.attr = attr


class first(Combinator):

    def __call__(note):

        def _composer(note):

            for i in self.attr_checks:
                if len(i) == 2 and self.attr is None:
                   if note.get(i[0]):
                       return i[1]
                elif attr is None:
                   v = note.get(i[0])
                   if v and v == i[1]:
                       return i[2]
                else:
                   v = note.get(self.attr)
                   if v and v == i[0]:
                       return i[1]

        c = _composer(note)
        if c is None: return
        return c.sound_generator_for(note)


class stack(Combinator):

    def __call__(self, note):

        sound_generators = []
        for i in self.attr_checks:
            if len(i) == 2 and self.attr is None:
               if note.get(i[0]):
                   v = i[1]
            elif attr is None:
               v = note.get(i[0])
               if v and v == i[1]:
                   v = i[2]
            else:
               v = note.get(self.attr)
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


class merge(Combinator):

    def __init__(self, attr, variants):
        attr_checks = []
        for key in sorted( variants ):
            attr_checks.append( (key, variants[key]) )
        self.attr_checks = attr_checks
        self.attr = attr

    def __call__(self, note):

        attrval = note.get(self.attr)
        if attrval is None:
            return

        leftv = None
        lastval = None
        for v in self.attr_checks:

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


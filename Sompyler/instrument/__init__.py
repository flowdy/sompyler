from operator import itemgetter
import re
from Sompyler.instrument.protopartial import ProtoPartial
from Sompyler.synthesizer.oscillator import Oscillator, CORE_PRIMITIVE_OSCILLATORS

def topological_sort(labeled_specs, lookup):
    """
    Modified version of:
    http://blog.jupo.org/2012/04/06/topological-sorting-acyclic-directed-graphs/
    """

    # This is the list we'll return, that stores each node/edges pair
    # in topological order.
    graph_sorted = []

    # Extract dependency information
    def find_dependencies(spec):
        dependencies = set()
        for i in specs:
            listdeps = re.findall(r'@([a-z]\w+)', i)
            for d in listdeps:
                if d not in labeled_specs:
                    pp = lookup(d)
                    if pp: labeled_specs[d] = pp
                    else: raise RuntimeError(
                        "Protopartial identifier irresoluble: " + d
                    )
                dependencies.add(d)
        return dependencies

    labeled_specs = dict(
        (label, find_dependencies(spec))
            for (label, spec) in labeled_specs
    )

    # Run until the unsorted graph is empty.
    while labeled_specs:

        acyclic = False
        for node, edges in list(labeled_specs.items()):
            for edge in edges:
                if edge in labeled_specs:
                    break
            else:
                acyclic = True
                del labeled_specs[node]
                graph_sorted.append(node)

        if not acyclic:
            circular_dependencies = labeled_specs.keys().join(", ")
            raise RuntimeError(
                "Circular dependencies could not be resolved among elements "
                     + circular_dependencies
            )

    return graph_sorted

def next_composer( attr, variants ):

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

def stacking_composer( attr, variants ):

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

def merging_composer( attr, variants ):

    attr_checks = []
    for key in sorted( variants ):
        attr_checks.append( (key, variants[key]) )

    def _composer(note):

        attrval = note.get(attr)
        if attrval is None:
            return

        leftv = None
        for v in attr_checks:

            if attrval == v[0]:
                return v[1].sound_generator_for(note)
            elif attrval < v[0]:
                if leftv is None:
                    return v[1].sound_generator_for(note)
                else:
                    dist = (attrval - leftv) * 1.0 / (v[0] - leftv)
                    return leftv.weighted_average( leftv, dist, v[1] )
            else:
                leftv = v[1]

        return leftv

    return _composer

VARIATION_COMPOSERS = {
    'next': next_composer,
    'stack': stacking_composer,
    'merge': merging_composer,
}

root_osc = CORE_PRIMITIVE_OSCILLATORS()

class Variation(object):

    __slots__ = (
        '_upper', 'base', '_variation_composer',
        'label_specs', '_partial_spec'
    )

    def __init__(
        self, upper, base, label_specs=None,
        _variation_composer=None, _partial_spec=None
      ):

        self._upper = upper
        self.base = base
        self.label_specs = label_specs or {}

        for i in topological_sorted(label_specs or {}, upper.lookup):
            label_specs[i] = ProtoPartial(
                upper, upper.lookup(i), label_specs, **label_specs[i]
            )

        self._variation_composer = _variation_composer

        self._partial_spec = _partial_spec

    def lookup(self, name):
        spec = self.label_specs.get(name)
        if spec is None and self._upper:
            spec = self._upper.lookup(name)
            self.label_specs[name] = spec
        return spec

    @classmethod
    def from_definition(cls, kwargs, upper=None):

        if not kwargs.has('TYPE'):
            Composer = None
        else:
            Composer = VARIATION_COMPOSERS[ kwargs.pop('TYPE') ]

        attribute = kwargs.pop('ATTR', None)

        label_specs = {}
        base_args = {}

        for attr in kwargs:
            if re.match('[a-z]\w+$', attr):
                label_specs[attr] = kwargs.pop(attr)
            elif re.match('[A-Z][A-Z]?$', attr):
                base_args[attr] = kwargs.pop(attr)

        self = cls(
            upper, ProtoPartial(**base_args), label_specs,
            _partial_spec=kwargs.pop('PARTIALS', None)
        )

        if Composer:
            self._variation_composer = Composer( attribute, dict(
                (
                  re.sub(r'^=', key)
                      if isinstance(key, str) else key,
                  Variation.from_definition(value)
                ) for key, value in kwargs.items()
            ))


    def sound_generator_for(self, note):

        if self._variation_composer:
            sg = self._variation_composer(note)
            if sg is not None: return sg

        # We need to make a sound generator from our partial_spec

        partials = self._partial_spec
        upper = self._upper
        while partials is None:
            if upper is None:
                partials = [ 100 ]
                break
            partials = upper._partial_spec
            upper = self._upper

        if not isinstance(partials, list):
            partials = [ { 0: (100, partials) } ]

        sympartial_points = []
        for pno, divs in enumerate(partials):
            pno += 1
            if not isinstance(divs, dict):
                divs = { 0: divs }
            for d, p in divs.items():
                freq_factor = pno * 2 ** (d*1.0/1200)
                if isinstance(p, tuple):
                    sympartial = self.lookup(p[1]).sympartial
                    volume = p[0]
                elif isinstance(p, int):
                    sympartial = self._base.sympartial
                    volume = p
                else:
                    raise TypeError(
                        p + " must be int (volume) or tuple (volume, label)"
                    )
                sympartial_points.append( (freq_factor, volume, sympartial ) )

        return SoundGenerator(self.base, sympartial_points, self.base)




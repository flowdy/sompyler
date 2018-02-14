from operator import itemgetter
from math import ceil
import re, yaml
from .protopartial import ProtoPartial
from . import combinators
from ...synthesizer import normalize_amplitude
from ...synthesizer.oscillator import Oscillator, CORE_PRIMITIVE_OSCILLATORS, Shape
from ...synthesizer.sound_generator import SoundGenerator
# from pdb import set_trace

root_osc = CORE_PRIMITIVE_OSCILLATORS()

for (key, value) in root_osc.items():
    root_osc[key] = ProtoPartial(None, None, {}, O=value)


class Instrument:
    __slots__ = ('root_variation',)

    def __init__(self, definition_file):
        with open(definition_file, 'r') as stream:
            instrument = yaml.load(stream)
        self.root_variation = Variation.from_definition(instrument['character'])

    def render_tone(self, pitch, length, stress, properties=None):

        note = {
            'pitch': pitch,
            'length': length,
            'stress': stress,
        }

        if properties:
            note.update(properties)
        else:
            properties = {}

        sg = self.root_variation.sound_generator_for(note)
        tone = sg.render(pitch, length, dict(
            (x, properties[x])
                for x in ('shaped_am', 'shaped_fm')
                if x in properties
        ))
        normalize_amplitude(tone, stress)

        return tone

# We need to make root_osc a Variation, but first we have to define
# that class:
class Variation(object):

    __slots__ = (
        'upper', 'base', '_variation_composer',
        'label_specs', '_profile', '_timbre', '_spread'
    )

    def __init__(
        self, upper, base, label_specs=None,
        _variation_composer=None, _profile=None,
        _timbre=None, _spread=None
      ):

        if label_specs is None:
            label_specs = {}
        self.upper = upper
        self.base = base
        self.label_specs = label_specs

        if upper:
            for i in topological_sort(label_specs, upper.lookup):
                label_specs[i] = ProtoPartial(
                    base, upper.lookup(i), label_specs, **label_specs[i]
                )

        self._variation_composer = _variation_composer

        self._profile = _profile
        self._timbre = _timbre
        self._spread = _spread

    def lookup(self, name):
        spec = self.label_specs.get(name)
        if spec is None and self.upper:
            spec = self.upper.lookup(name)
            self.label_specs[name] = spec
        return spec

    @classmethod
    def from_definition(cls, kwargs, upper=None):

        if not isinstance(kwargs, dict):
           raise TypeError("Not a dictionary: " + kwargs)

        if upper is None:
            upper = root_osc

        if not 'TYPE' in kwargs:
            Composer = None
        else:
            Composer = getattr(combinators, kwargs.pop('TYPE'))

        attribute = kwargs.pop('ATTR', None)

        label_specs = {}
        base_args = {}

        for attr in list( kwargs.keys() ):
            if not isinstance(attr, str):
               continue
            elif re.match('[a-z]\w+$', attr):
                label_specs[attr] = kwargs.pop(attr)
            elif re.match('[A-Z][A-Z]{0,2}$', attr):
                base_args[attr] = kwargs.pop(attr)

        timbre = kwargs.pop('TIMBRE', None)
        if timbre is not None:
            timbre = Shape.from_string(timbre)

        self = cls(
            upper, ProtoPartial(
                base=None, upper=upper.base,
                pp_registry={ 'LOOK_UP': upper.lookup },
                **base_args
            ),
            label_specs,
            _profile=kwargs.pop('PROFILE', None),
            _spread=kwargs.pop('SPREAD', None),
            _timbre=timbre
        )

        if Composer:
            self._variation_composer = Composer( attribute, dict(
                (
                  re.sub(r'^=', key, '')
                      if isinstance(key, str) else key,
                  Variation.from_definition(value, self)
                ) for key, value in kwargs.items()
            ))

        return self


    def sound_generator_for(self, note):

        if self._variation_composer:
            sg = self._variation_composer(note)
            if sg is not None:
                return sg

        sympartial_points = []

        # ---------------
        # We need to make a sound generator from our partial_spec
        # -----

        partials = None
        upper = self
        while upper and partials is None:
            partials = upper._profile
            upper = upper.upper
        self._profile = partials

        # Our partial spec might be just a simple label.
        # Resolve it for only one partial.
        if isinstance(partials, str):
            partials = [ (100, partials) ]

        def piter():
            for p in partials:
                if isinstance(p, list):
                    yield from (int(x) for x in p)
                else:
                    yield p

        for p in piter():
            deviance = 0

            if isinstance(p, tuple):
                sympartial = self.lookup( p[1] ).sympartial()
                volume = p[0]
            elif isinstance(p, dict):
                volume = p['V']
                deviance = p.get('D', 0)
                labels = self.label_specs
                labels['LOOK_UP'] = upper.lookup
                sympartial = ProtoPartial(
                    None, self.base, labels, **p
                ).sympartial()
            elif isinstance(p, str):
                m = re.match(r'(\d+)\s+(\w+)', p)
                if m:
                    sympartial = self.lookup( m.group(2) ).sympartial()
                    volume = int(m.group(1))
                else:
                    raise TypeError(
                        "Could not parse string: " + p
                    )
            elif isinstance(p, int):
                sympartial = None
                volume = p
            else:
                raise TypeError(
                    p + " must be int (volume) or tuple (volume, label)"
                )

            sympartial_points.append( (deviance, volume, sympartial ) )

        boundary_symp = None if (
            sympartial_points[0][2] or sympartial_points[-1][2]
        ) else self.base.sympartial()

        spread = None
        upper = self
        while upper and spread is None:
            spread = upper._spread
            upper = upper.upper
        self._spread = spread or []

        soundgen = SoundGenerator.shape(
            boundary_symp, sympartial_points, boundary_symp, self._spread
        )

        # -------------------
        # Let us add resonance to the partials. The strength factor
        # depends on its frequency.
        # ---

        timbre = None
        upper = self
        while upper and timbre is None:
            timbre = upper._timbre
            upper = upper.upper
        self._timbre = timbre

        min_diff = 1.0
        prior_coord_x = soundgen.coords[0].x
        for c in soundgen.coords[1:]:
            diff = c.x - prior_coord_x
            if diff < min_diff:
                min_diff = diff
            prior_coord_x = c.x

        partitions = ceil( 1.0 / min_diff )
        amplifications = timbre.render(
            1, adj_length=( note['pitch'] * soundgen.length )
        )
        for c in soundgen.coords[1:]:
            c.y += amplifications[ int( len(amplifications) * c.x )-1 ] - 1

        return soundgen


root_osc = Variation(
    None, None, root_osc,
    _profile=[ 100 ],
    _timbre=Shape.from_string("20000:1;1,1")
)

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
        LABEL_REF_RX = r'@([a-z]\w+)'
        dependencies = set()
        for i in spec.values():
            if isinstance(i, dict):
                listdeps = [ re.findall(LABEL_REF_RX, j) for j in i.keys() ]
            listdeps = re.findall(LABEL_REF_RX, i)
            for d in listdeps:
                if d not in labeled_specs:
                    pp = lookup(d)
                    if pp: labeled_specs[d] = pp
                    else: raise RuntimeError(
                        "Protopartial reference irresoluble: " + d
                    )
                dependencies.add(d)
        return dependencies

    labeled_dependency_sets = {}
    for label, spec in labeled_specs.items():
        deps = find_dependencies(spec)
        labeled_dependency_sets[label] = deps

    # Run until the unsorted graph is empty.
    while labeled_dependency_sets:

        acyclic = False
        for node, edges in list(labeled_dependency_sets.items()):
            for edge in edges:
                if edge in labeled_specs:
                    break
            else:
                acyclic = True
                del labeled_dependency_sets[node]
                graph_sorted.append(node)

        if not acyclic:
            circular_dependencies = labeled_dependency_sets.keys().join(", ")
            raise RuntimeError(
                "Circular dependencies could not be resolved among elements "
                     + circular_dependencies
            )

    return graph_sorted


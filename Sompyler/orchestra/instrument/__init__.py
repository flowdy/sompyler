from operator import itemgetter
import re
from Sompyler.orchestra.instrument.protopartial import ProtoPartial
import Sompyler.orchestra.instrument.combinators
from Sompyler.synthesizer import normalize_amplitude
from Sompyler.synthesizer.oscillator import Oscillator, CORE_PRIMITIVE_OSCILLATORS, Shape
from Sompyler.synthesizer.sound_generator import SoundGenerator
from math import ceil

root_osc = CORE_PRIMITIVE_OSCILLATORS()

for (key, value) in root_osc.items():
    root_osc[key] = ProtoPartial(None, None, {}, O=value)

class Instrument(object):
    __slots__ = ('root_variation',)

    def __init__(self, definition):
        self.root_variation = Variation(definition)

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
        tone = sg.render(pitch, length, {
            (x, properties[x])
                for x in ('shaped_am', 'shaped_fm')
                if x in properties
        })
        normalize_amplitude(tone)

        return tone

# We need to make root_osc a Variation, but first we have to define
# that class:
class Variation(object):

    __slots__ = (
        'upper', 'base', '_variation_composer',
        'label_specs', '_partial_spec', '_timbre_spec'
    )

    def __init__(
        self, upper, base, label_specs=None,
        _variation_composer=None, _partial_spec=None,
        _timbre_spec=None,
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

        self._partial_spec = _partial_spec
        self._timbre_spec = _timbre_spec

    def lookup(self, name):
        spec = self.label_specs.get(name)
        if spec is None and self.upper:
            spec = self.upper.lookup(name)
            self.label_specs[name] = spec
        return spec

    @classmethod
    def from_definition(cls, kwargs, upper=None):

        if upper is None:
            upper = root_osc

        if not 'TYPE' in kwargs:
            Composer = None
        else:
            Composer = getattr(combinators, kwargs['TYPE'])

        attribute = kwargs.pop('ATTR', None)

        label_specs = {}
        base_args = {}

        timbre = kwargs.pop('TIMBRE', None)
        if timbre is not None:
            timbre = Shape.from_string(timbre)

        for attr in kwargs.keys():
            if re.match('[a-z]\w+$', attr):
                label_specs[attr] = kwargs.pop(attr)
            elif re.match('[A-Z][A-Z]?$', attr):
                base_args[attr] = kwargs.pop(attr)

        self = cls(
            upper, ProtoPartial(
                base=None, upper=upper.base,
                pp_registry={ 'LOOK_UP': upper.lookup },
                **base_args
            ),
            label_specs,
            _partial_spec=kwargs.pop('PARTIALS', None),
            _timbre_spec=timbre
        )

        if Composer:
            self._variation_composer = Composer( attribute, dict(
                (
                  re.sub(r'^=', key)
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

        # ---------------
        # We need to make a sound generator from our partial_spec
        # -----

        partials = None
        upper = self
        while upper and partials is None:
            partials = upper._partial_spec
            upper = upper.upper
        self._partial_spec = partials

        # Our partial spec might be just a simple label.
        # Resolve it for only one partial.
        if isinstance(partials, str):
            partials = [ { 0: (100, partials) } ]

        sympartial_points = []
        for pno, divs in enumerate(partials):
            pno += 1
            if not isinstance(divs, dict) or 'V' in divs:
                divs = { 0: divs }
            for d in sorted( divs.keys() ):
                p = divs[d]
                freq_factor = pno * 2 ** (d*1.0/1200)
                if isinstance(p, tuple):
                    sympartial = self.lookup( p[1] ).sympartial()
                    volume = p[0]
                elif isinstance(p, dict):
                    volume = p.pop('V')
                    sympartial = ProtoPartial(
                        None, self.base, self.label_specs,
                        **p
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
                sympartial_points.append( (freq_factor, volume, sympartial ) )

        boundary_symp = None if (
            sympartial_points[0] or sympartial_points[-1]
        ) else self.base.sympartial

        soundgen = SoundGenerator(
            boundary_symp, sympartial_points, boundary_symp
        )

        # -------------------
        # Let us add resonance to the partials. The strength factor
        # depends on its frequency.
        # ---

        timbre = None
        upper = self
        while upper and timbre is None:
            timbre = upper._timbre_spec
            upper = upper.upper

        self._timbre_spec = timbre

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
    _partial_spec=[ 100 ],
    _timbre_spec=Shape.from_string("20000:1;1,1")
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
        dependencies = set()
        for i in spec:
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


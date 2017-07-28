from operator get itemgetter
import re
from Sompyler.instrument.protopartial import ProtoPartial
from Sompyler.synthesizer.oscillator import Oscillator, STANDARD_OSC_FUNC

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

root_osc = STANDARD_OSC_FUNC()

for i in root_osc:
    root_osc[i] = Oscillator(osc_func=root_osc[i])

class Variation(object):

    __slots__ = ('_upper', 'base', 'label_specs')

    def __init__( self, upper, base, kwargs, label_specs=None):

        self._upper = upper
        self.base = base
        self.label_specs = label_specs or {}

        for i in topological_sorted(label_specs or {}, upper.lookup):
            label_specs[i] = ProtoPartial(
                upper, upper.lookup(i), label_specs, **label_specs[i]
            )

    def lookup(self, name):
        spec = self.label_specs.get(name)
        if spec is None and self._upper:
            spec = self._upper.lookup(name)
            self.label_specs[name] = spec
        return spec

    def from_definition(kwargs, upper=None):

        if not kwargs.has('TYPE'):
            cls = 'Variation'
        else:
            type = kwargs.pop('TYPE')
            if type == 'dispatch':
                cls = Dispatcher
            elif type == 'interpolate':
                cls = Interpolator
            elif type == 'stack':
                cls = Stacker
            else:
                raise Exception("Unknown variation type: {}".format(type))

        attribute = kwargs.pop('ATTR', None)

        label_specs = {}
        base_args = {}
        for attr in kwargs:
            if re.match('[a-z]\w+$', attr):
                label_specs[attr] = kwargs.pop(attr)
            elif re.match('[A-Z][A-Z]?$', attr):
                base_args[attr] = kwargs.pop(attr)

        return cls(upper, ProtoPartial(**base_args), kwargs, label_specs)

class Interpolator(Variation):

    __slots__ = ('attribute', 'attr_specs')

    def __init__(self, attribute, kwargs):
        Variation.__init__(self, kwargs)
        self.attribute = attribute
        self.attr_specs = []
        for (i, props) in sorted(
            kwargs.iteritems(), key=itemgetter(0)
        ):
            value = float(i)
            props = Variation.from_definition( props, self )
            self.attr_specs.append((value, props))

     def sound_generator(self, note):
         raise NotImplemented

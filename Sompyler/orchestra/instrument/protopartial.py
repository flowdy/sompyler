# -*- coding: utf-8 -*-

from ...synthesizer.sympartial import Sympartial
from ...synthesizer.modulation import Modulation
from ...synthesizer.envelope import Envelope, Shape
import re

ABBREV_ARGS = {
    'A': 'attack',
    'S': "sustain",
    'B': "boost",
    'R': "release",
    'AM': "amplitude_modulation",
    'FM': "frequency_modulation",
    'WS': "wave_shape",
    'O': "oscillator" # value merely informational (not used)
}

ENV_ARGS = ('A', 'S', 'B', 'R')
OSC_ARGS = ('AM', 'FM', 'WS')

SHAPES = ENV_ARGS + ('WS',)
MODS = ('AM', 'FM')

class ProtoPartial:
    """
    Manage all properties. Inherit them top-down from base of the variation
    or from the protopartial labelled the same from an upper variation, and get
    a sympartial instance which you can render tones with.
    """

    __slots__ = ('_base', '_upper', '_cache') + tuple(
        '_' + i for i in ABBREV_ARGS
    )

    def __init__( self, base, upper, pp_registry, other=None, **args ):

        def refresolver(name):
            pp = pp_registry.get(name)
            if pp is None:
                pp = pp_registry['LOOK_UP'](name)
            if pp is None:
                raise ValueError('Name cannot be resolved: ' + name)
            return pp

        if other:
            if not other.startswith('@'):
                raise ValueError('other argument must reference a @label')
            base = refresolver( other[1:] )

        self._base = base
        self._upper = upper
        self._cache = {}

        for prop in ABBREV_ARGS.keys():

            value = args.get(prop)
            if value is None:
                continue

            elif prop == "O" and isinstance(value, str):
                if not value.startswith('@'):
                     value = '@' + value

            if not isinstance(value, dict):
                value = { value: 1 }

            res, total_weight = None, 0

            for value, weight in value.items():

                if isinstance(value, str):
                    if value.startswith('@'):
                        value = value[1:]
                        pp = refresolver(value)
                        value = pp.get(prop)
                    elif prop in SHAPES:
                        value = Shape.from_string(value)
                    elif prop in MODS:
                        value = Modulation.from_string(value, pp_registry)

                if res:
                    total_weight += weight
                    res = res.weighted_average(
                        res, weight / total_weight, value
                    )
                else:
                    res, total_weight = value, weight

            setattr(self, '_' + prop, res)

        if self.get('O') is None:
            raise Exception("ProtoPartial instance missing oscillator")

    def get (self, attr):
        """ Look up attribute first in own attributes, then in the ancestry
            of named variation. If it is not found there, try the base and its ancestry.
        """

        privm = '_' + attr
        value = getattr(self, privm, None)

        if value is not None:
            return value
        elif attr in self._cache:
            return self._cache[attr]

        for m in (self._upper, self._base):
            if m is None: continue
            value = getattr(m, privm, m.get(attr))
            if value is not None:
                self._cache[attr] = value
                return value

    def sympartial ( self ):

        env_args = {}; osc_args = {}

        for each in ENV_ARGS:
             val = self.get(each)
             if val: env_args[ ABBREV_ARGS[each] ] = val

        for each in OSC_ARGS:
             val = self.get(each)
             if val: osc_args[ ABBREV_ARGS[each] ] = val

        return Sympartial(
            Envelope(**env_args), 
            self.get('O').derive(**osc_args)
        )
        

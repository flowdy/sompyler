# -*- coding: utf-8 -*-

from __future__ import division
from Sompyler.synthesizer.sympartial import Sympartial
from Sompyler.synthesizer.modulation import Modulation
from Sompyler.synthesizer.envelope import Shape
import re

ABBREV_ARGS = {
    'A': 'attack',
    'S': "sustain",
    'B': "boost",
    'R': "release",
    'AM': "amplitude_modulation",
    'FM': "frequency_modulation",
    'WS': "wave_shape",
}

ENV_ARGS = ('A', 'S', 'B', 'R')
OSC_ARGS = ('AM', 'FM', 'WS')

SHAPES = ENV_ARGS + ('WS',)
MODS = ('AM', 'FM')

class ProtoPartial(object):
    """
    Manage all properties 
    """

    __slots__ = ('_base', '_upper', '_cache',) + tuple(
        '_' + i for i in ABBREV_ARGS
    )

    def __init__( self, base, upper, pp_registry, **args ):
        self._base = base
        self._upper = upper
        self._cache = {}

        osc = args.pop('O')
        if osc:
            self._O = pp_registry[osc].O
        if self._O is None:
            raise Exception("ProtoPartial instance missing oscillator")

        for prop in ABBREV_ARGS.keys():
            value = args.get(prop)
            if value is None:
                setattr(self, prop, None)
                continue
            elif value.startswith('@'):
                value = getattr( pp_registry[value[1:]], prop)()
            if prop not in ABBREV_ARGS:
                raise AttributeError
            if prop in SHAPES:
                value = Shape.from_string(value)
            elif prop in MODS:
                value = Modulation.from_string(value, pp_registry)
            setattr(self, '_' + prop, value)

    for i in ABBREV_ARGS: exec """
        {0} = property(lambda (self, obj): obj.lookup_attr("{0}"), None, None)
    """.format(i)

    def _lookup_attr (self, attr):
        """ Look up attribute first in own attributes, then in the ancestry
            of named variation. If it is not found there, try the base and its ancestry.
        """

        value = getattr(self, '_' + attr, None)

        if value is not None:
            return value
        elif self._cache.has(attr):
            return self.cache[attr]

        for m in (self._upper, self._base):
            if m is None:
                continue
            privm = '_' + attr
            value = (
                getattr(m, privm) if hasattr(m, privm)
                                else m._lookup_attr(attr)
            )
            if value is not None:
                self._cache[attr] = value
                return value

    def sympartial ( self ):

        env_args = {}; osc_args = {}

        for each in ENV_ARGS:
             val = getattr(self, each)()
             if val: env_args[ ABBREV_ARGS[i] ] = val

        for i in OSC_ARGS:
             val = getattr(self, each)()
             if val: osc_args[ ABBREV_ARGS[i] ] = val

        return Sympartial(
            Envelope(**envelope_args), 
            self.O().derive(**oscillator_args)
        )
        

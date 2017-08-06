# -*- coding: utf-8 -*-

from __future__ import division
from Sompyler.synthesizer.sympartial import Sympartial
from Sompyler.synthesizer.modulation import Modulation
from Sompyler.synthesizer.envelope import Envelope, Shape
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

class ProtoPartial(object):
    """
    Manage all properties. Inherit them top-down from base of the variation
    or from the protopartial labelled the same from an upper variation, and get
    a sympartial instance which you can render tones with.
    """

    __slots__ = ('_base', '_upper', '_cache') + tuple(
        '_' + i for i in ABBREV_ARGS
    )

    def __init__( self, base, upper, pp_registry, **args ):
        self._base = base
        self._upper = upper
        self._cache = {}

        for prop in ABBREV_ARGS.keys():
            value = args.get(prop)
            if value is None:
                setattr(self, '_' + prop, None)
                continue
            elif prop == "O":
                if isinstance(value, str):
                    pp = pp_registry['LOOK_UP'](value)
                    value = pp.get('O')
            elif value.startswith('@'):
                value = value[1:]
                pp = pp_registry.get( value )
                if pp is None:
                    pp = pp_registry['LOOK_UP'](value)
                value = pp.get(prop)
            if prop in SHAPES:
                value = Shape.from_string(value)
            elif prop in MODS:
                value = Modulation.from_string(value, pp_registry)
            setattr(self, '_' + prop, value)

        if self._O is None:
            raise Exception("ProtoPartial instance missing oscillator")

    def get (self, attr):
        """ Look up attribute first in own attributes, then in the ancestry
            of named variation. If it is not found there, try the base and its ancestry.
        """

        value = getattr(self, '_' + attr, None)

        if value is not None:
            return value
        elif attr in self._cache:
            return self.cache[attr]

        for m in (self._upper, self._base):
            if m is None:
                continue
            privm = '_' + attr
            value = (
                getattr(m, privm) if hasattr(m, privm)
                                else m.get(attr)
            )
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
        

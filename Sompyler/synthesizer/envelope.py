# -*- coding: utf-8 -*-

from __future__ import division
from Sompyler.synthesizer import SAMPLING_RATE
from Sompyler.synthesizer.shape import Shape

class Envelope(object):
    """ Threesome of attack, sustain and release phases of a partial tone.

    Please note that in contrast to the ADSR envelope combining linearly
    shaped attack, decay, sustain and release phase, as is conventionally used
    in digital synthesis, in our ASR model, formed by bezier curves, a decay
    part may be optionally merged into either the attack or the sustain.

    A decay part at the end of the attack phase will not be extended for longer
    tones, a decay in the beginning of the sustain phase will. Hence, sustain
    must not increase in the end. When it increases, it is almost certainly an
    error, that the user wishes so unlikely. To make sympartial specification
    less error-prone, this is checked and an exception is thrown.

    A boost shape is needed to level up a sustain ending in a volume too low.

    """

    def __init__(self, attack, sustain=None, boost=None, release=None):
        self.attack = (
            attack if isinstance(attack, Shape)
                  else Shape.from_string(attack)
        )

        if sustain:
            self.sustain = (
                sustain if isinstance(sustain, Shape)
                        else Shape.from_string(sustain)
            )
            sust_penult_y, sust_ult_y = self.sustain.y_slice(-2, None, None)
            if sust_penult_y < sust_ult_y:
                raise Exception("Last two coords may not rise")
        else:
            self.sustain = None

        if release: self.release = (
            release if isinstance(release, Shape)
                    else Shape.from_string(release)
        )
        else:
            self.release = None

        initial_y, final_y = self.attack.edgy()

        if initial_y:
            raise Exception("Attack does not start at 0dB")

        if final_y:
            if not self.release:
                raise Exception("Attack not finalized, neither is a "
                      + "release phase defined"
                    )

            if self.release.edgy()[1]:
                raise Exception("Release phase does not end at 0dB")

        elif ( self.sustain or self.release ):
            raise Exception(
                "Sustain and release defined after finalized attack"
            )

        if boost:
            if not (self.sustain and self.release):
                raise Exception(
                    "boost connects sustain and release phases which is "
                  + "requires both to be defined"
                )
            self.boost = (
                boost if isinstance(boost, Shape)
                      else Shape.from_string(boost)
            )
            boost.rescale_y( attack.y_max )
        
        else: self.boost = None

    def derive ( **args ):

        for i in 'attack', 'sustain', 'release', 'boost':
            if args.get(i):
                continue
            mine = getattr(self, i, None)
            if mine:
                args[i] = mine

        self.__class__( **args )


    def render (self, duration=0):
        """ considers different prolongation for each phase:
         * attack: cannot be prolonged or trimmed. Static length.
         * sustain: prolonged or trimmed by linear interpolation
         * release: scaled proportionally extending the sustain
        """

        overlength = duration and duration > self.attack.length
        fill = duration - self.attack.length if overlength else 0
    
        sustain = self.sustain or CONSTANT_SUSTAIN

        results = self.attack.render(SAMPLING_RATE)
    
        if fill: results.extend(
            sustain.render(
                SAMPLING_RATE,
                y_scale=results[-1],
                adj_length=fill,
                final_boost=self.boost
            )
        )
    
        if results[-1]:
            results.extend(
                self.release.render(
                    SAMPLING_RATE,
                    y_scale=results[-1],
                    adj_length=True
                )
            )
        
        return results

    @classmethod
    def weighted_average (cls, left, dist, right):

        phases = {}

        if left is right:
            return left

        for p in 'attack', 'sustain', 'boost', 'release':

            lattr = getattr(left, p)
            rattr = getattr(right, p)

            if lattr and rattr and lattr is not rattr:
                phases[p] = Shape.weighted_average( lattr, dist, rattr )
            else:
                phases[p] = lattr or rattr

        (phases['release'] or phases['attack']).coords[-1].y = 0

        return cls( **phases )

CONSTANT_SUSTAIN = Shape((1,1), (1,1))


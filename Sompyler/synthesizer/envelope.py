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

    """

    def __init__(self, attack, sustain=None, release=None):
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

        if release: self.release = (
            release if isinstance(release, Shape)
                    else Shape.from_string(release)
        )

        initial_y, final_y = self.attack.edgy()

        if initial_y:
            raise Exception("Attack does not start at 0dB")

        if ( self.sustain is None
         and self.release   is None
         and not final_y == 0
        ):
           raise Exception(
               "Attack not finalized despite lacking sustain and release: "
              +"Last coordinate must be y=0, but is really {}".format(final_y)
           )
        elif not final_y:
           raise Exception(
               "Attack finalized (ends at 0dB) but no sustain or release phase"
              +" is defined"
           )
        elif not self.release or self.release.edgy()[1]:
           raise Exception(
              "Release phase not defined or does not end at 0dB"
           )


    CONSTANT_SUSTAIN = Shape((0,1), (1,1))

    def render (self, duration=None):
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
                adj_length=fill
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

        for p in 'attack', 'sustain', 'release':

            lattr = getattr(left, p)
            rattr = getattr(right, p)

            if lattr and rattr:
                phases[p] = Shape.weighted_average( lattr, dist, rattr )
            elif lattr or rattr:
                phases[p] = lattr or rattr

        return cls( **phases )



# -*- coding: utf-8 -*-

import codecs
import yaml
import re
import numpy as np
from sound_generator import SoundGenerator
from operator import itemgetter

_beats_per_minute = None
_beat_length = None
general_tone_mapper = None

class Instrument:

    def __init__(self, tones, closeness, stereo_position, tuning, character):
        self.tone_mapper = tones
        self.play_tone = find_path_to_timbre(character).render
        self.tuning = general_tone_mapper(tuning)
        self.closeness = int(closeness)
        self.stereo_position = int(stereo_position)
        assert abs(self.stereo_position) < 91

    @staticmethod
    def from(file):
        with codecs.open(file, encoding="utf-8") as splidef:
            spli = yaml.safe_load(splidef)
        if "sompyler-instrument" in spli['MIME']:
        del spli['MIME']
        del spli['label']
        del spli['description']
        del spli['copyright']
        del spli['legalese']
        return Instrument(**spli)

    @staticmethod
    def configure (bpm, beat_length=None, fps=None):
        _beats_per_minute = int(bpm)
        _beat_length = float(beat_length)
        # only necessary in initial configuring
        if fps: SoundGenenerator.FRAMES_PER_SECOND = int(fps)

    @staticmethod
    def find_path_to_timbre(character):
        if type(character) == 'list':
            return ToneEmitter(character)
        elif character[ "_interpolate" ]:
            return Interpolator(character)
        else:
            return Dispatcher(character)

    def _parse_note (self, note):

        pitch, length, properties = note.split(" ", 2)
        pitch = self.tuning(pitch)
        length = float(length)
        stress = re.match(r'^(\d+)', properties)
        
        if stress:
            stress = stress.group(1)
            re.sub(r'^\d+\s+','', properties)

        prop_d = {}
        for i in properties.split(" "):
            
            m = re.match(r'^(\w+)=(\S+)$', i)
            if m:
                key, value = m.groups
                prop_d[key] = value
            else:
                raise Exception("Note property {} cannot be parsed".format(i))

        prop_d['pitch'] = pitch
        prop_d['length'] = length
        if stress:
            prop_d['stress'] = stress

        return prop_d

        
    def play_beat (self, d):

        meta = d.pop('meta') if 'meta' in d else {}

        beat = lambda: np.zeros(
           _beat_length * 240 / _beats_per_minute
               * SoundGenerator.FRAMES_PER_SECOND
        )

        for key in sorted(x for x in d.keys, key=float):
            notes = d[key]
            offset = float(key)

            if not isinstance(notes, list):
                notes = [notes]

            samples = []
            for note in notes:
                note_d = meta.copy()
                note_d.update(_parse_note(note))
                tone = self.play_tone(note) 

                # TODO: consider ties across barlines
                overlength = offset + _note_d['length']
                if overlength > _beat_length:
                    np.array_split(tone, overlength -   
                samples.append(tone)
             
class ToneEmitter(object):

    def __init__(self, character)
        soundgen = SoundGenerator(character)
        self._emitter = lambda note: soundgen

    def recurse_init (self, d):
        for i, v in d.iteritems():
            d[i] = Instrument.find_path_to_timbre(v)

    def render(self, note, args):
        self._emitter(note).render(note)

class Dispatcher(ToneEmitter):

    def __init__(self, d):

        attr = d.pop('_dispatch') if '_dispatch' in d else None

        if attr:
            assert not attr == '_dispatch'
            self._emitter = lambda note: note[attr] and d[ note[attr] ]
            self.recurse_init(d)

        else:
            self._render = lambda note: next(
                d[x] for x in note if note[x] and d[x]
            )

class Interpolator(ToneEmitter):

    def __init__(self, d):
        attr = d.pop( '_interpolate' )
        assert not attr == '_interpolate'
        self.recurse_init(d)
        grades = sorted(x for x in d.items, key=itemgetter(0))
        self._emitter = lambda note: interpolate_for(grades, attr, note)

    def interpolate_for(grades, note):

        it = iter(grades)
        last_item = next(it)
        demanded = note[attr]

        if demanded is None:
            raise RuntimeError(
                "No note attribute {} to interpolate according to"
            )

        for x in it:
            leftval = int(last_item[0])
            rightval = int(x[0])
            if demanded <= rightval:
               position = (demanded - leftval) / (rightval - leftval)
               gen0 = last_item[1]
               gen1 = x[1]
               break
            last_item = x

        return Generator.merge(
            gen0._render(note), position, gen1._render(note)
        )

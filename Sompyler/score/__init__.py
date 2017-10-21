from yaml import load_all
from Sompyler.tone_mapper import get_mapper_from
from Sompyler.score.measure import Measure
from Sompyler.score.stressor import Stressor
from Sompyler.score.channel import Channel
import re

class Score(object):

    def __init__(self, filename):

        self._yamliter = load_all(open(filename))

        self.metadata = next(yamliter)

        self._tuner = get_mapper_from(
            self.metadata['tone_mapping']
                or 'test_examples/tones_euro_de+en.splt'
        ) 

        self._channels = self.metadata.pop('channels')
        for name, ch_data in self._channels.items():
            if isinstance(ch_data, str):
                 direction, distance, instrument = ch_data.split()
                 tuning = self._tuner()
            else:
                 direction, distance, instrument, tuning = (
                     ch_data.pop(i, None) for i in (
                         'direction', 'distance', 'instrument', 'tuning'
                     )
                 )
                 tuning = self._tuner(tuning)
                 
            self._channels[name] = Channel(
                self.metadata['room'],
                direction, distance, instrument, tuning
            )

        for ch in self._channels.values():
            ch.set_amplitudes()

    def note_feed(self):

        prev_measure = None

        for m in self._yamliter:
            m = Measure(m, previous=prev_measure)
            for ch_name, cbmeasure in m:
                cbmeasure.channel = self._channels[ cbmeasure.channel ]
                cbnotes = []

                for chord in cbmeasure:
                    chord_notes = [ note for note in chord ]
                    sum_weights = sum(n.stress[0] for n in chord_notes)
                    for note in chord_notes:
                        note.stress = (
                            note.stress[0] / sum_weights * note.stress[1]
                        )
                    cbnotes.extend(chord_notes)

                max_stress = max(n.stress for n in cbnotes)
                if max_stress < 1:
                    max_stress = 1
                for note in cbnotes:
                    note.stress /= max_stress
                    yield note

            prev_measure = m



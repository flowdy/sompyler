from yaml import load_all
from Sompyler.synthesizer import SAMPLING_RATE
from Sompyler.tone_mapper import get_mapper_from
from Sompyler.score.measure import Measure
from Sompyler.score.stressor import Stressor
from Sompyler.score.stage import Stage
import re, sys, numpy
from os import path

class Score(object):

    def __init__(self, file):

        self._filename = file.name
        self._yamliter = load_all(file)

        metadata = next(self._yamliter)

        tuner = get_mapper_from(
            metadata.get('tone_mapping')
                or 'test_examples/tones_euro_de+en.splt'
        ) 

        self.stage = Stage(
            metadata['stage'].pop('_space', '1:0|1:0'),
            metadata['stage'],
            tuner
        )

        self._distinct_notes = [ dict() ]


    def notes_feed_1st_pass(self, monitor=lambda: None):

        def flattened_notes():

            prev_measure = None

            for m in self._yamliter:
                m = Measure(m, stage=self.stage, previous=prev_measure,
                        **m.pop('_meta', {})
                )

                for vbmeasure in m:
                    vbnotes = []

                    for chord in vbmeasure:
                        chord_notes = [ note for note in chord ]
                        sum_weights = 1 # sum(n.stress[0] for n in chord_notes)
                        for note in chord_notes:
                            note.stress = (
                                note.stress[0] / sum_weights * note.stress[1]
                            )

                        vbnotes.extend(chord_notes)

                    max_stress = max(n.stress for n in vbnotes)
                    if max_stress < 1:
                        max_stress = 1
                    for note in vbnotes:
                        note.stress /= max_stress
                        yield note

                prev_measure = m

        def get_abspath_to( instrument_spec_fn ):
        
            score_directory = path.dirname( path.abspath(self._filename) )
        
            fn = instrument_spec_fn + '.spli'
        
            if not path.isabs(fn):
                absfile = path.join(score_directory, fn)
                if not path.isfile(absfile):
                    absfile = path.join(sys.path[0], 'instruments', fn)
                if not path.isfile(absfile):
                    raise RuntimeException( instrument_spec_fn
                        + " is neither found in same directory as the score "
                          " file nor in the global instruments/ directory "
                   )
        
            return absfile

        for note in flattened_notes():

            note_id = self._distinct_notes[0].get( note )

            if note_id:
                distinct_note = self._distinct_notes[ note_id ]
                distinct_note.occurrences.extend( note.occurrences )
                monitor( note_id, note.occurrences[0] )
                continue

            else:
                note_id = len(self._distinct_notes)
                self._distinct_notes.append(note)
                self._distinct_notes[0][ note ] = note_id
                monitor( note_id, note.occurrences[0], str(note) )

                yield (
                    note_id, get_abspath_to(note.instrument), note.pitch,
                    note.length, note.stress, note.properties
                )

    def set_length_for_note(self, note_id, num_samples):
        self._distinct_notes[ note_id ].num_samples = num_samples

    def notes_feed_2nd_pass(self):

        def occiter(occ, num_samples):
            for offset, position in occ:
                offset = int(round( SAMPLING_RATE * offset ))
                position = numpy.array([position]).repeat(num_samples, axis=0)
                yield (slice(offset, offset + num_samples), position)

        total_end_offset = 0
        for note in self._distinct_notes[1:]:

            end_offset = int(round(
                SAMPLING_RATE * max(o[0] for o in note.occurrences)
            )) + note.num_samples

            if end_offset > total_end_offset:
                total_end_offset = end_offset

        return total_end_offset, (
            ( num+1, occiter(note.occurrences, note.num_samples) )
                for num, note in enumerate(self._distinct_notes[1:])
        )

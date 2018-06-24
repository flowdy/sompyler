from yaml import load_all
import re, sys, numpy, csv, pdb
from collections import defaultdict
from os import path, readlink, getpid
from ..synthesizer import SAMPLING_RATE
from ..tone_mapper import get_mapper_from
from .measure import Measure
from .stressor import Stressor
from .stage import Stage
from .note import Note

class Score:

    def __init__(self, file):

        self._yamliter = load_all(file)
        self.directory = path.dirname( path.abspath(file.name) )

        try:
            linkedfile = readlink(file.name)
            self.real_directory = path.dirname(linkedfile)
        except OSError:
            self.real_directory = self.directory

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

    def load_prev_run_cache(self, registry_file, instr_check, tonefile_check):
    
        prev_run_cache = {}
    
        instruments = { v.instrument for v in self.stage.voices.values() }
        uptodate_instruments = set()
    
        for instrument in instruments:
    
            fn = instrument + '.spli'
            
            if path.isabs(fn):
                absfile = fn
            else:
                absfile = path.join(self.real_directory, fn)
                if not path.isfile(absfile):
                    absfile = path.join(sys.path[0], '../instruments', fn)
                if not path.isfile(absfile):
                    raise FileNotFoundError( fn
                        + " is neither found in same directory as the score"
                          " file nor in the Sompyler's instruments/ directory"
                    )
    
            if instr_check( instrument, absfile ):
                uptodate_instruments.add( instrument )

        registry_file.seek(0)
        csvreader = csv.reader(registry_file)
        note_cnt = 1
        for t in csvreader:
            note = Note.from_csv(*t)
            prev_run_cache[ note ] = note_cnt
            note_cnt += 1

        notes = [None] * note_cnt
        notes[0] = prev_run_cache
        for note, note_id in prev_run_cache.items():
            notes[note_id] = note

        self._registry_file = registry_file
        self._distinct_notes = notes
        self._tonefile_check = tonefile_check
        self._uptodate_instruments = uptodate_instruments
        self._notes_new_from_index = note_cnt


    def notes_feed_1st_pass(self, monitor=lambda: None):

        def flattened_notes():

            prev_measure = None
            prev_cumlength = 0
            deferred = []

            mno = 0

            for m in self._yamliter:
                mno += 1
                monitor('NEXTMEASURE', mno)
                m = Measure(m, stage=self.stage, previous=prev_measure,
                        **m.pop('_meta', {})
                )
                mnotes = defaultdict(list)
                ticks = {1}

                for orig_offset, pos_note in deferred:
                    mnotes[-orig_offset].append(pos_note)
                    ticks.add( min(m.length, pos_note[1].length_ticks) )

                abslength = m.stressor.cumlen

                for vbmeasure in m:

                    for chord in vbmeasure:
                        chord_notes = []
                        for offset, pos_note in chord:
                            mnotes[offset].append(pos_note)
                            ticks.add(offset)
                            ticks.add(min(
                                abslength - offset, pos_note[1].length_ticks
                            ))
                            chord_notes.append(pos_note[1])
                        sum_weights = (
                                sum(n.stress[0] for n in chord_notes)
                              / len( chord_notes )
                            ) 
                        for note in chord_notes:
                            note.stress = (
                                note.stress[0] / sum_weights * note.stress[1]
                            )

                (last_elem, *ticks) = sorted(ticks)
                unit = ticks[-1]
                for i in ticks:
                    diff = i - last_elem
                    if diff < unit:
                        unit = diff
                    last_elem = i

                lencalc = m.get_length_calculator(unit)

                deferred.clear()

                for offset, pos_notes in mnotes.items():
                    real_offset = 0 if offset < 0 else offset

                    for (position, note) in pos_notes:

                        lenticks = min(
                                abslength - real_offset, note.length_ticks
                            )
                        note.length_ticks -= lenticks

                        offset_secs, length_secs = lencalc(
                                real_offset - max(m.measure_cut,0), lenticks
                            )

                        offset_secs += prev_cumlength
                        if note.length_ticks == 0 and offset < 0:
                            offset_secs = abs(offset)

                        note.length_secs += length_secs

                        if note.length_ticks > 0:
                            deferred.append((
                                abs(offset) if offset < 0 else offset_secs,
                                (position, note)
                            ))
                        else:
                            note.add_occurrence(
                                    offset_secs, *position
                                )
                            yield note

                prev_cumlength += lencalc(
                        max(m.measure_cut,0), m.length
                    )[1]

                prev_measure = m

        for note in flattened_notes():

            note_id = self._distinct_notes[0].get( note )

            if note_id:

                distinct_note = self._distinct_notes[note_id]
                first_use = distinct_note.is_unused()
                distinct_note.add_occurrences_of(note)

                if not first_use:
                    monitor(
                        "REUSENOTE", note_id, next(note.occurrence_iter())
                    )
                    continue

                elif (
                       note.instrument in self._uptodate_instruments
                       and self._tonefile_check(note_id)
                     ):

                    monitor(
                        "REUSENOTE_FRUN", note_id,
                        next(note.occurrence_iter()), str(note)
                    )
                    continue

            else:
                note_id = len(self._distinct_notes)
                self._distinct_notes[0][note] = note_id
                self._distinct_notes.append(note)

            monitor("NEWNOTE",
                    note_id, next(note.occurrence_iter()),
                    str(note)
                )

            yield (
                    note_id, note.instrument, note.pitch, note.stress,
                    note.length_secs, note.properties
                )


    def set_length_for_note(self, note_id, length):
        note = self._distinct_notes[note_id]
        note.num_samples = length

    def notes_feed_2nd_pass(self):

        csv_w = csv.writer(self._registry_file)
        for note in self._distinct_notes[self._notes_new_from_index:]:
            csv_w.writerow(note.to_csvible_tuple())

        self._registry_file.close()

        def occiter(occ, num_samples):
            for offset, position in occ:
                offset = int(round( SAMPLING_RATE * offset ))
                position = numpy.array([position]).repeat(num_samples, axis=0)
                yield slice(offset, offset + num_samples), position

        total_end_offset = 0
        unused_notes = []

        for note in self._distinct_notes[1:]:

            if note.is_unused():
                continue

            end_offset = int(round(
                SAMPLING_RATE * max(o[0] for o in note.occurrence_iter())
            )) + note.num_samples

            if end_offset > total_end_offset:
                total_end_offset = end_offset

        def note_iter():
            for note_id, note in enumerate(self._distinct_notes[1:]):
                note_id += 1
                if note.is_unused():
                    unused_notes.append(note_id)
                    continue
                yield note_id, occiter(
                        note.occurrence_iter(), note.num_samples
                    )

        return total_end_offset, unused_notes, note_iter()

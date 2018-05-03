from __future__ import print_function
from .instrument import Instrument
from ..score import Score
from ..score.note import Note
from tempfile import mkdtemp
import sys, os, numpy, traceback, pickle

cached_files_dir = None

def play(score_fh, workers=None, monitor=None):

    score = Score(score_fh)

    initialize_worker( mkdtemp(prefix='sompyler_cached-notes-') )

    if workers is None or workers > 1:
        import multiprocessing 
        pool = multiprocessing.Pool(
            processes=workers,
            initializer=initialize_worker,
            initargs=[cached_files_dir]
        )
        imap = pool.imap_unordered
    else:
        imap = map

    notes_cnt  = 0
    errors_cnt = 0

    max_end_offset = 0

    prev_run_cache = {}

    uptodate_instruments = set()

    for v in score.stage.voices:
        cached_instrument_path = os.path.join(
                cached_files_dir, hash(v.instrument) + '.instr'
            )
        if os.path.isfile(cached_instrument_path) and os.path.getmtime(
            cached_instrument_path ) > os.path.getmtime(v.instrument):
            uptodate_instruments.add( v.instrument )
        else:
            pickle.dump( Instrument(v.instrument), cached_instrument_path )

    registry_path = os.path.join(cached_files_dir, "registry")
    if os.path.isfile(registry_path):
        with open(registry_path) as f:
            csvreader = csv.reader(f)
        note_cnt = 1
        for note in Note.fake_instances_from_csv(csvreader):
            tone = numpy.load(tone_id_to_filename(note_cnt, "snd.npy"))
            if len(tone.shape) != 1:
                raise RuntimeError("Numpy shape of tones must be 1")

            if note.instrument in uptodate_instruments:
                prev_run_cache[ note ] = (note_cnt, len(tone))
            else:
                prev_run_cache[ note ] = (note_cnt, None)

            note_cnt += 1

    with open(registry_path, "a+") as f:
        write_csv = csv.writer(f)

    def get_note(note):
        if note in prev_run_cache and prev_run_cache[note][1] is not None:
            return note, *prev_run_cache[ note ]
        else:
            if note in prev_run_cache:
                note_id = prev_run_cache[ note ][0]
            else:
                note_cnt += 1
                note_id = note_cnt
                write_csv(note.to_csvible_tuple())
            return note, *render_tone(note_id, note)

    mon = monitor or (lambda n, o, d=None: None)
    for note, note_id, length in imap(
            get_note, score.notes_feed_1st_pass(mon)
        ):
        
        if length is not None:
            score.register_unseen_note(note, note_id) 
            mon(note, note.occurrences[0], str(note))
            note.num_samples = length
        else:
            raise NoteRenderingFailure(note_id)

    total_length, distinct_notes_iter = score.notes_feed_2nd_pass()

    samples = numpy.zeros( (total_length, 2) )

    for note_id, occurrences in distinct_notes_iter:
        tone = numpy.load(
            tone_id_to_filename(note_id, "snd.npy")
        ).reshape(-1, 1)
        for slc, position in occurrences:
            samples[slc] += position * tone

    return samples


def initialize_worker(tempdir):
    global cached_files_dir
    cached_files_dir = tempdir


current_instrument = ("", None)

def get_cached_instrument(instrument):
    global current_instrument

    if current_instrument[0] == instrument:
        instrument = current_instrument[1]
    else:

        with open(os.path.join(
            cached_files_dir,
            hash(instrument) + ".instr"
            ), "rb") as f: 

            i = pickle.load(f)

        current_instrument = (instrument, i)
        instrument = i

    return instrument


def render_tone(note_id, note):

    instrument = get_cached_instrument(note.instrument)

    try:
        tone = instrument.render_tone(
            note.pitch, note.length, note.stress, note.properties
        )
        numpy.save(tone_id_to_filename(note_id, "snd"), tone )
        return note_id, len(tone)

    except Exception as e:
        with open(tone_id_to_filename(note_id, "err"), "w") as err:
            err.write(traceback.format_exc(e))
        return note_id, None


def tone_id_to_filename(id, ext):
    return os.path.join( cached_files_dir, "{:05d}.{}".format(id,ext) )


class NoteRenderingFailure(Exception):

    def __init__(self, note_id):
        self.note_id = note_id

    def orig_info(self):
        with open(tone_id_to_filename(self.note_id, "err"), "r") as f:
            return f.read()

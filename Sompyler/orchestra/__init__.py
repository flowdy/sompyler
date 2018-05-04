from __future__ import print_function
from .instrument import Instrument
from ..score import Score
from ..score.note import Note
from tempfile import mkdtemp
import sys, os, numpy, traceback, pickle

cached_files_dir = None

def play(score_fn, workers=None, monitor=None):

    if os.path.isdir(score_fn):
        score_fn = os.path.join(score, "/score")

    score_fh = open(score_fn, 'r')
    score = Score(score_fh)

    initialize_worker(
            score.directory if os.path.isfile(
                os.path.join(score.directory, ".use_dir_as_cache")
            )
            else get_prepared_tempdir(score_fn)
        )

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

    registry_path, prev_run_cache = load_prev_run_cache(score)

    instruments = uptodate_instruments_set(score)

    def retrieve_or_render_tone(new_note_id, note):

        note_id = prev_run_cache.get(note, 0)
        cache_file = tone_id_to_filename(note_id, "snd.npy")
        if note_id > 0 and os.path.isfile(cache_file):
            tone = numpy.load(cache_file)
            if len(tone.shape) != 1:
                raise RuntimeError("Numpy shape of tones must be 1")
            return note, note_id, -len(tone)
        else:
            if not note_id:
                note_id = note_cnt + new_note_id
            else:
                note_id *= -1 # so it is positive
            return note, note_id, render_tone(note_id, note)

    if not monitor:
        monitor = lambda n, o, d=None: None

    new_notes = set()

    for note, note_id, length in imap(
            retrieve_or_render_tone, score.notes_feed_1st_pass(monitor)
        ):
        
        if length is None:
            raise NoteRenderingFailure(note_id)

        score.cache_note(note, note_id) 
        mon(
                note_id, note.occurrences[0],
                str(note) if length > 0
                          else str(note) + ", re-used from former run"
            )
        note.num_samples = abs(length)

        if length > 0:
            new_notes.add( (note_id, note) )

        else: # protect against deletion
            _ = prev_run_cache.pop(note,'')

    with open(registry_path, "a") as f:
        write_csv = csv.writer(f)
        for _, note in sorted(new_notes, key=lambda i: i[0]):
            write_csv.writerow(note.to_csvible_tuple())

    for orphaned_note_id in prev_run_cache.values():
        os.unlink( tone_id_to_filename(orphaned_note_id, "snd.npy") )

    total_length, distinct_notes_iter = score.notes_feed_2nd_pass()

    samples = numpy.zeros( (total_length, 2) )

    for note_id, occurrences in distinct_notes_iter:
        tone = numpy.load(
            tone_id_to_filename(note_id, "snd.npy")
        ).reshape(-1, 1)
        for slc, position in occurrences:
            samples[slc] += position * tone

    return samples

def get_prepared_tempdir(scorefile):
    tempdir = mkdtemp(prefix='sompyler_cached-notes-')
    os.symlink( os.path.abspath(scorefile), os.path.join(tempdir, "score") )
    open( os.path.join(tempdir, ".use_dir_as_cache"), 'w' ).close()

    return tempdir


def initialize_worker(tempdir):
    global cached_files_dir
    cached_files_dir = tempdir

def load_prev_run_cache(score):

    prev_run_cache = {}

    instruments = { v.instrument for v in score.stage.voices.values() }
    uptodate_instruments = set()

    for instrument in instruments:

        fn = instrument + '.spli'
        
        if os.path.isabs(fn):
            absfile = fn
        else:
            absfile = os.path.join(score.real_directory, fn)
            if not os.path.isfile(absfile):
                absfile = os.path.join(sys.path[0], '../instruments', fn)
            if not os.path.isfile(absfile):
                raise FileNotFoundError( fn
                    + " is neither found in same directory as the score"
                      " file nor in the Sompyler's instruments/ directory"
                )

        cached_instrument_path = os.path.join(
                cached_files_dir, str(hash(instrument)) + '.instr'
            )

        if os.path.isfile(cached_instrument_path) and os.path.getmtime(
                cached_instrument_path
            ) > os.path.getmtime(absfile):
            uptodate_instruments.add( instrument )

        else:
            with open(cached_instrument_path, 'w') as f:
                 pickle.dump( Instrument(absfile), f )

    registry_path = os.path.join(cached_files_dir, "registry")
    if os.path.isfile(registry_path):
        with open(registry_path, 'r') as f:
            csvreader = csv.reader(f)
            note_cnt = 1
            for note in Note.fake_instances_from_csv(csvreader):
                prev_run_cache[ note ] = (
                    note_cnt
                        if note.instrument in uptodate_instruments
                        else -note_cnt
                           # ^ negation to just re-use id for new note
                    )
                note_cnt += 1

    return registry_path, prev_run_cache


current_instrument = ("", None)

def get_cached_instrument(instrument):
    global current_instrument

    if current_instrument[0] == instrument:
        instrument = current_instrument[1]
    else:

        cache_file = os.path.join(
                cached_files_dir, str(hash(instrument)) + ".instr"
            )

        with open(cache_file, "rb") as f: 
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
        numpy.save( tone_id_to_filename(note_id, "snd"), tone )
        return len(tone)

    except Exception as e:
        with open(tone_id_to_filename(note_id, "err"), "w") as err:
            err.write(traceback.format_exc(e))
        return None


def tone_id_to_filename(id, ext):
    return os.path.join( cached_files_dir, "{:05d}.{}".format(id,ext) )


class NoteRenderingFailure(Exception):

    def __init__(self, note_id):
        self.note_id = note_id

    def orig_info(self):
        with open(tone_id_to_filename(self.note_id, "err"), "r") as f:
            return f.read()

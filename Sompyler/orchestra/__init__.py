from .instrument import Instrument
from ..score import Score
from ..score.note import Note
from tempfile import mkdtemp
import sys, os, numpy, traceback, pickle
import pdb

cached_files_dir = None

def instrument_check(instrument, absfile):

    cached_instrument_path = os.path.join(
            cached_files_dir, str(hash(instrument)) + '.instr'
        )

    instrument_is_cached = os.path.isfile(cached_instrument_path)

    if (instrument_is_cached
            and os.path.getmtime(cached_instrument_path)
                > os.path.getmtime(absfile)
        ):
        return True

    else:
        with open(cached_instrument_path, 'wb') as f:
            pickle.dump( Instrument(absfile), f )
        return not instrument_is_cached

def play(score_fn, workers=None, monitor=None):
    global cached_files_dir

    if os.path.isdir(score_fn):
        score_fn = os.path.join(score_fn, "score")

    score_fh = open(score_fn, 'r')
    score = Score(score_fh)

    cached_files_dir = (
            score.directory if os.path.isfile(
                os.path.join(score.directory, ".use_dir_as_cache")
            )
            else get_prepared_tempdir(score_fn)
        )

    score.load_prev_run_cache(
            registry_file=open(os.path.join(cached_files_dir, 'registry'),'a+'),
            instr_check=instrument_check,
            tonefile_check=lambda tone_id: os.path.isfile(
                    tone_id_to_filename(tone_id, "snd.npy")
                )
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

    if monitor is None:
        monitor = lambda *m, **n: None

    for note_id, length in imap(
            render_tone, score.notes_feed_1st_pass(monitor)
        ):
        
        if length is None:
            raise NoteRenderingFailure(note_id)

        score.set_length_for_note(note_id, length)

    score_fh.close()

    total_length, unused, distinct_notes_iter = score.notes_feed_2nd_pass()

    monitor( "ASSEMBLE", total_length, 2 )

    samples = numpy.zeros( (total_length, 2) )

    for note_id, occurrences in distinct_notes_iter:
        tone = numpy.load(
            tone_id_to_filename(note_id, "snd.npy")
        ).reshape(-1, 1)
        for slc, position in occurrences:
            samples[slc] += position * tone

    monitor( "DELETEORPHANS", len(unused) )

    with open(
            os.path.join(cached_files_dir, "unused_tone.files"), "w"
        ) as unused_fh:
        for note_id in unused:
            print(tone_id_to_filename(note_id, "snd.npy"), out=unused_fh)

    return samples, cached_files_dir


def get_prepared_tempdir(scorefile):
    tempdir = mkdtemp(prefix='sompyler_cached-notes-')
    os.symlink( os.path.abspath(scorefile), os.path.join(tempdir, "score") )
    open( os.path.join(tempdir, ".use_dir_as_cache"), 'w' ).close()

    return tempdir


def initialize_worker(tempdir):
    global cached_files_dir
    cached_files_dir = tempdir


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


def render_tone(info):

    note_id, instrument, pitch, stress, length, properties = info

    instrument = get_cached_instrument(instrument)

    try:
        tone = instrument.render_tone(
            pitch, length, stress, properties
        )
        numpy.save( tone_id_to_filename(note_id, "snd"), tone )
        length = len(tone)

    except Exception as e:
        with open(tone_id_to_filename(note_id, "err"), "w") as err:
            err.write(traceback.format_exc(e))
        length = None

    return note_id, length


def tone_id_to_filename(id, ext):
    return os.path.join( cached_files_dir, "{:05d}.{}".format(id,ext) )


class NoteRenderingFailure(Exception):

    def __init__(self, note_id):
        self.note_id = note_id

    def orig_info(self):
        with open(tone_id_to_filename(self.note_id, "err"), "r") as f:
            return f.read()

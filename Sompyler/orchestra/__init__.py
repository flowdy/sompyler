from __future__ import print_function
from Sompyler.orchestra.instrument import Instrument
from Sompyler.score import Score
from tempfile import mkdtemp
import sys, os, numpy, traceback

cached_files_dir = None


def play(score_fh, workers=None, verbosity=False):

    max_end_offset = 0

    initialize_worker( mkdtemp() )

    if workers == 1:
        import itertools
        imap = itertools.imap
    else:
        import multiprocessing 
        pool = multiprocessing.Pool(
            processes=workers,
            initializer=initialize_worker,
            initargs=[cached_files_dir]
        )
        imap = pool.imap_unordered

    notes_cnt  = 0
    errors_cnt = 0

    score = Score(score_fh)

    for note_id, length in imap(render_tone, score.notes_feed_1st_pass(mon)):
        
        if length is not None:
            score.set_length_for(n_hash, length) 
        else:
            raise NoteRenderingFailure(note_id)

    total_length, distinct_notes_iter = score.notes_feed_2nd_pass()

    samples = numpy.zeros( (2, total_length) )

    for note_id, occurrences in distinct_notes_iter:
        tone = numpy.load( tone_id_to_filename(note_id, "snd") )
        for slc, position in occurrences:
            samples[slc] += position * tone

    return samples


current_instrument = ("", None)

def initialize_worker(tempdir):
    global cached_files_dir
    cached_files_dir = tempdir

def render_tone(info):
    global current_instrument

    note_id, instrument, pitch, length, stress, properties = info

    if current_instrument[0] == instrument:
        instrument = current_instrument[1]
    else:
        i = Instrument(instrument)
        current_instrument = (instrument, i)
        instrument = i

    try:
        tone = instrument.render_tone(
            pitch, length, stress, properties
        )
        numpy.save(tone, tone_id_to_filename(note_id, "snd") )
        return note_id, len(tone)

    except Exception as e:
        with open(tone_id_to_filename(note_id, "err"), "w") as err:
            f.write(traceback.format_exc(err))
        return note_id, None


def tone_id_to_filename(id, ext):
    return os.path.join( cached_files_dir, "{:05d}.{}".format(id,ext) )

class NoteRenderingFailure(Exception):

    def __init__(self, note_id):
        self.note_id = note_id

    def orig_info(self):
        with open(tone_hash_to_filename(note_id, "err"), "r") as f:
            return f.read()

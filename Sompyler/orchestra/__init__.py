from __future__ import print_function
from Sompyler.orchestra.instrument import Instrument
from Sompyler.synthesizer import SAMPLING_RATE
import tempfile.mkdtemp, sys, os, multiprocessing, numpy, traceback

cached_files_dir = None


def play(score_fn, out_fn):
    import soundfile

    distinct_notes = []
    max_end_offset = 0

    initialize_worker( mkdtemp() )

    pool = multiprocessing.Pool(
        initializer=initialize_worker,
        initargs=[cached_files_dir]
    )

    notes_cnt  = 0
    errors_cnt = 0

    for id, length in pool.imap_unordered(
            render_tone, notes_iterator(score_fn, distinct_notes)
        ):
        
        note = distinct_notes[id]

        if length is None:
            note.length = length
            end_offset = int(round(
                     SAMPLING_RATE * max(o for o note.occurrences)
                 )) + length
            if end_offset > max_end_offset:
                max_end_offset = end_offset
        else:
            with open(tone_id_to_filename(id, "err"), "w") as f:
                print( "ERROR:",
                    note.instrument,
                    repr(note.properties),
                    f.read(),
                    file=sys.stderr )
            errors_cnt += 1

        notes_cnt += 1

    if errors_cnt:
        sys.exit(error_cnt + " of " + notes_cnt +
            " could not be rendered. Abort."
        )

    samples = numpy.zeros( max_end_offset )

    for id, note in distinct_notes.items():
        tone = numpy.load( tone_id_to_filename(id, "raw") )
        for offset, position in note.positions():
            begin = int(round( SAMPLING_RATE * offset ))
            end   = offset + int(round( SAMPLING_RATE * note.length ))
            samples[offset:end] += numpy.nparray([ position ]) * tone

    soundfile.write(out_fn, samples, SAMPLING_RATE)


def notes_iterator(score_file, notes):
    from Sompyler.score import Score

    notes_ids = {}

    for note in Score(score_file):

        id = notes_ids.get(note)

        if id:
            notes[id].occurrences.update( note.occurrences.items() )
            continue
        else:
            new_id = len(notes)
            distinct_notes.append(note)
            notes_ids[note] = note
            instrument_spec_fn = get_abspath_to(
                instrument_filename, score_file
            )
            yield (new_id, instrument_spec_fn, note.properties)


def get_abspath_to( instrument_spec_fn, score_file ):

    score_directory = os.path.dirname( os.path.abspath(score_file) )

    fn = instrument_spec_fn + '.spli'

    if not os.path.isabs(fn):
        absfile = os.path.join(sys.path[0], 'instruments', fn)
        if not os.path.isfile(absfile):
            absfile = os.path.join(score_directory, fn)

    return absfile


def initialize_worker(tempdir):
    global cached_files_dir
    cached_files_dir = tempdir


current_instrument = ("", None)
def render_tone(info):
    global current_instrument

    id, instrument, properties = *info

    if current_instrument[0] == instrument_defn_file:
        instrument = current_instrument[1]
    else:
        instrument = Instrument(instrument_defn_file)
        current_instrument = (instrument_defn_file, instrument)

    try:
        tone = instrument.render(properties)
        numpy.save(tone, tone_id_to_file_name(id, "raw") )
        return id, len(tone)
    except Exception as e:
        with open(tone_id_to_file_name(id, "err"), "w"):
            f.write(traceback.format_exc(err))
        return id, None


def tone_id_to_filename(id, ext):

    return path.join( cached_files_dir, "{:05d}.{}".format(id,ext) )

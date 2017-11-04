from Sompyler.orchestra import play
from Sompyler.synthesizer import normalize_amplitude
from Sompyler import synthesizer
import soundfile
import argparse

def mon(note_id, occurrence, description=None):

    print ("New note" if description else "Reuse note"),
    print note_id, "@"+occurrence,
    if description:
        print ":", description
    else:
        print "."

def process(options):

    synthesizer.SAMPLING_RATE = options['samplerate']
    synthesizer.BYTES_PER_CHANNEL = options['samplewidth']

    format = options['format'] or 'PCM_' + synthesizer.BYTES_PER_CHANNEL

    try:
        samples = play(
            options['score_file'], options['workers'],
            monitor if options.verbose else None
        )
    except NoteRenderingFailure as e:
        sys.stderr.write(e.orig_info() + "\n")
        raise

    normalize_amplitude(samples)

    soundfile.write(
        options['out_file'], samples,
        synthesizer.SAMPLING_RATE, format=format
    )

    return 0

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        description="Convert a Sompyler score, accompanied with "
                    "instrument specifications linked therein, to audio file"
    )
    parser.add_argument('score_file',
        type=argparse.FileType('r'),
        help="File containing the Sompyler score in YAML syntax"
    )
    parser.add_argument('out_file',
        type=argparse.FileType('w'),
        help="File to which the audio data is written"
    )
    parser.add_argument('--samplerate',
        default=44100,
        type=int,
        help="How much frames per second"
    )
    parser.add_argument('--samplewidth',
        default=2,
        choices=(1,2,3,4),
        help="How much bytes per frame to use"
    )
    parser.add_argument('--format',
        default=None,
        type=str,
        help="Subtype of output as is supported by libsnd for that filetype"
    )
    parser.add_argument('--workers',
        default=1,
        type=int,
        help="How many processes are used to render tones in parallel"
    )
    parser.add_argument('--verbose', '-v',
        default=False,
        action='store_true',
        help="Display calculated information to every note"
    )
    exit(process(parser.parse_args()))
    

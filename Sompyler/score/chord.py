from Sompyler.score.note import Note

class Chord(object):

    def __init__(
           self, total_offset, measure_offset, voice,
           stress, calc_span, notes
        ):

        self.total_offset = total_offset
        self.offset_ticks = measure_offset
        self.voice        = voice
        self.stress       = stress
        self.calc_span    = calc_span
        self.notes        = notes

    def __iter__(self):

        for note in self.notes:
            yield Note(
                instrument=self.voice.instrument,
                stress=self.stress,
                properties=note,
                calc_span=self.calc_span,
                total_offset=self.total_offset,
                offset_ticks=self.offset_ticks,
                position=self.voice.position,
                tuner=self.voice.tuning
            )

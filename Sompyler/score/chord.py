from Sompyler.score.note import Note

class Chord(object):

    def __init__(
           self, total_offset, measure_offset, channel,
           stress, notes
        ):

        self.total_offset = total_offset
        self.offset       = offset
        self.channel      = channel
        self.stress       = stress
        self.calc_span    = calc_span
        self.notes        = notes

    def __iter__(self):

        for note in self.notes:
            yield Note(
                instrument=channel.instrument,
                stress=stress,
                properties=note,
                calc_span=self.calc_span,
                total_offset=self.total_offset,
                offset_ticks=self.offset_ticks,
                position=self.channel.position,
                tuner=self.channel.tuning
            )

from .note import Note

class Chord:

    def __init__(
           self, offset, voice, stress, notes
        ):

        self.offset_ticks = offset
        self.voice        = voice
        self.stress       = stress
        self.notes        = notes

    def __iter__(self):

        for note in self.notes:
            yield Note.from_score(
                instrument=self.voice.instrument,
                dynamic_stress=self.stress,
                properties=note,
                offset_ticks=self.offset_ticks,
                position=self.voice.position,
                tuner=self.voice.tuning
            )

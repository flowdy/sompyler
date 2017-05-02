Sompyler
========

This is an off-line (not a real-time) synthesizer for sound design,
as well as for symphony and song composition. However, it is pre-alpha
and cannot fulfill that claim, yet. Of course, I could just *use* other
well elaborated and proven software synthesizers like Csound, but programing
yet another alternative is much more fun. So, as yet it is just a way of mine
to learn Python, as well as theory of acoustics and music at once.

Basics
------

There are a bunch of definition files that are used to describe the
audio output into a wave file.

  1. Tone system and mapping. In the distribution there is a file to define
     the common tune of 440Hz for the 49th key (A4) with 12 tone steps per
     octave. Use that to play western music. These settings accord to the MIDI
     standard. 88 notes can be referenced by english or german names.

  2. Orchestra: Which instruments are situated where on virtual stage. 

  3. Instruments: Their sound character (overall "timbre") and variations
     thereof that take effect depending on the properties of a played note.
     The character is specified in multiple dimensions:

       * Partials have a frequency relative to the base frequency of a tone.
         Ideally the factor is integer, but slight deviation in cent can be
         specified.

       * Each partial has its share of the volume

       * Each partial has its own OSR envelope, that is actually defined as a
         bezier curve. This should make for a smoother impression than the
         conventional linear and artificial ADSR envelope that is not very
         natural (nothing in nature is truly linear). Plus, a partial can be
         modified by frequency modulation, amplitude modulation (both shapable
         too), wave shaping.

       * Variations are interpolated based on scalar properties of a note,
         like base frequency or stress.

       * Variations can also be selected based on discrete properties, e.g.
         if the sustain pedal of a piano is pressed.

  4. Score files: One file for each bar/measure defines which instruments play
     which note with what pitch, what length and offset from zero position in that
     bar, and optionally other properties like an own frequency modulation shape.

System requirements
-------------------

  * Python 2.7
  * PyYAML

TODO
----

As of March 28, 2017 I intend to elaborate

 * multiple partials configuration to be selected according to frequency
 * interpolation of partial shape between neighbouring frequency-based configuration

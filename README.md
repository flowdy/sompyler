Sompyler
========

This is an off-line (not a real-time) synthesizer for sound design,
as well as for symphony and song composition.

However, it is pre-alpha and cannot fulfill that claim, yet.

Why I program yet another software synthesizer?
-----------------------------------------------

Of course, I could just use other well elaborated and proven software
synthesizers like Csound, but programing yet another alternative is much more
fun. So, as yet it is just a way of mine to learn Python, as well as theory of
acoustics and music at once.


Basics
------

The sounding character of instruments and the music can both be 
described in compact YAML syntax (or JSON which is actually a subset of YAML).
The specification uses concepts of music theory and acoustics. Feed that data
to Sompyler so it constructs an according audio file. The tool calculates
and carefully stratifies partial tones onto each other. It realizes the notes
in accordance with harmony, rhythm and dynamics regarding each measure.

Quality, which basically depends on the input and creator's
obsession with details, can easily reach beyond conventional software 
synthesis based on MIDI events and loaded soundfonts. Sompyler music can even
come pretty close to "real music", that is played by humans on physical
instruments. Though it will always be distinguishable from that kind of
music for the experienced ear. Just do not expect overly much so you might
get surprised.

There are a bunch of YAML definition files that are used to describe the
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

       * Each partial has its share of the volume, specified on the logarhithmic
         scale normalized to 100 dB. So, e.g. a partial with a share of 80dB
         has the tenth of the sound pressure of a partial with 100dB.

       * Each partial has its own ASR envelope, that is actually defined as a
         bezier curve. Whether an optional decay part is integrated in the attack
         or the sustain phase is to be considered carefully. Bezier curves should
         make for a smoother impression than the conventional linear and artificial
         ADSR envelope that is not very natural (nothing in nature is truly linear).
         Plus, a partial can be modified by frequency modulation, amplitude
         modulation (both shapable too), wave shaping.

       * Variations are interpolated based on scalar properties of a note,
         like base frequency or stress.

       * Variations can also be selected based on discrete properties specific to an
         instrument, e.g. if the sustain pedal of a piano is pressed.

  4. Below the orchestra definition (s.a. item 2) multiple YAML documents follow, each
     a measure. Every measure is a map of channels associated with a nested map of offsets
     again associated with the specification of at least one note with its properties:
     pitch, length and stress. A measure can have metadata covering tempo and stress, that
     can be constant or a linearly rising/falling gradient, and also a stress pattern.
     Lacking metadata is taken from preceeding measures. Every metadata item can be derived
     for specific channels.

As yet, sound generators can be defined. [Learn how](doc/instrument-definition.md)

Prerequisites
-------------

### User

Ability to edit raw text files with a powerful text editor. There will be no
"official" user interface that hides the text definition stuff behind eye-candy
widgets. Sompyler works according to the pure Unix philosophy, like a compiler,
hence the name:

    $ sompyler input.spls output.flac
    [text scrolling over the screen. You are not expected to read it, except
    to trace errors if any.]

Others are welcome to program GUIs for sompyler, of course.

### Hardware

To make music with Sompyler, you should use a strong multi-core CPU and much RAM,
depending on the score, since the complete sound file is built tone- and partialwise
all in memory. Sound hardware is not required.

### Software

Besides of Python 2.7.x (as a Python newbie I postpone rewrite for 3.x, since
version 2.x is more present in my job and self-confusion is not very much fun)
one needs only three packages:

  * PyYAML – to parse YAML or JSON text
  * soundfile – to transform the calculated raw samples into a file, e.g. FLAC
  * Numpy (mostly included) – calculation of each sample

That is it. No dependencies to sound fonts, sound system layers or MIDI stuff.
But again, not depending on it is easy given that users will not be able to
perform live. If Sompyler is ever suitable for professional music production,
it is stuck to studio work. Its stage fright is legendary.

Later I intend to program a tool to generate Sompyler YAML data from MIDI
events, but first there are more important things to do.

While the sompyler is in alpha state, I rather focus development of core features
than getting it to run on other systems than mine, which is a Debian GNU/Linux.

Sufficiently fast CPU and much RAM (at least 1G, depending on the length of the
score you want to compile) is recommended since sound data is purely calculated
i.e. without external sound fonts and things like that.

Copyright & License
-------------------

(C) 2017 Florian 'flowdy' Heß

See LICENSE containing the General public license, version 3.

Sompyler is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Sompyler is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Sompyler. If not, see <http://www.gnu.org/licenses/>.

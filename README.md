Sompyler
========

Sompyler is a sound design and music composition tool, a software synthesizer,
a puristic approach of a digital audio workstation (DAW) for text-based interface
fans. It works in off-line (versus real-time) mode. Do not expect that a pressed key
instantly emits a sound, rendering Sompyler unfit for live performance at least insofar I
am developing myself, leaving the domain of live performance to people of professional
knowledge with professional tools.

At least its foundation is my hopefully comprehensive understanding of acoustic and music
theory.

The basic workflow of the sompyler user:
----------------------------------------

  1. Make sure there are instrument definition files. A set of instrument definitions are
     included in the official code distribution. Feel free to make your own, load one from
     the internet, whatever. Instrument definitions can either be added to the sompyler
     installation so they can be shared between projects, or they can be stored inside a
     specific project directory. The files are expected to end `*.spli`.
     [Learn how to define a sompyler instrument](doc/instrument-definition.md)

  2. Make the score file, extension `*.spls`. The score file is a sequence of YAML text
     streams. The first YAML document describes the score, i.e. title, composer, etc., and
     also the stage. The stage definition declares all voices which can be sent notes in
     the subsequent YAML documents of the stream, measure for measure. A voice is basically
     a path of an instrument definition file, interpreted as relative to sompyler installation
     directory or the music project directory (automatically detected), plus a stereo position
     and the intensity i.e. the distance to the listener, and optionally other properties.

  3. Input following command: `scripts/sompyle path/to/your/score-file.spls /tmp/output.$ext`
     with $ext being `wav`, `flac` or `ogg`.

  4. Listen and go to step 1 or 2 for another iteration of improvement. 

Currently, sounds are rendered anew in subsequent runs of Sompyler. This admittedly makes gradual
improvement and trying tedious, which is why persistent caching is planned. Ideally, after your mere
rearrangements of sounds without changing their length, volume or inner structure the cached data
is only reassembled on the timeline and distributed between the channels in no time.

Prerequisites
-------------

### User

Know-how and ability to edit raw text files with a powerful text editor. There will be no
"official" user interface that hides the text definition stuff behind eye-candy
widgets. Sompyler works according to the pure Unix philosophy, i.e. reasonable data in,
audio (PCM) data out. It works just like a compiler builds an executable program from,
the sources hence the name:

    $ scripts/sompyle input.spls output.flac
    [Text scrolling over the screen when --verbose flag is on.]


### Hardware

To make music with Sompyler, you should use a strong multi-core CPU and much RAM,
depending on the score, since the complete sound file is built tone- and partialwise
all in memory.

Dedicated sound production hardware is not required.

Dedicated high quality audio playback hardware is recommended so a bad listening
experience is likely to result from errors in the definition you need to correct,
instead of cheap electronic devices.


### Software

Sompyler has very few dependencies:

  * It is written in Python 3, hence it needs that interpreter to run.
  * PyYAML – to parse YAML or JSON text
  * soundfile – transforms the calculated raw samples into a file, e.g. FLAC
  * Numpy – sample calculation
  * optionally Cython – turbo-boost calculation of envelopes of partial tones

That is it. No dependencies to third-party sound fonts, sound system layers or MIDI stuff.
Admittedly, not depending on these is easy given that users will not be able to
perform live. If Sompyler is ever suitable for professional music production,
it is probably stuck to studio work. Its stage fright is legendary as the quality of
emmitted sound is entirely in users controle.


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

Sompyler
========

This is a synthesizer for sound, symphony and song design. However,
it is pre-alpha and cannot fulfill that claim, yet.

It currently supports sounds composed of fundamental and overtones ("partials").
Amplitude and or frequency of each partial can be sine-modulated independently.

Is there anybody who expects that little exercise in python programming to be suitable for
serious sound design? No? Fine, neither do I. ;) Real instruments produce a wide spectrum of
overtones. I am not sure python can handle these numbers with that approach, at most far from
meeting real-time needs.

Based on code from "ivan_onys" published January 16, 2015 on
[Stack Overflow](http://stackoverflow.com/questions/8299303/generating-sine-wave-sound-in-python).


System requirements
-------------------

  * Python 2.7
  * PyAudio library wrapping PortAudio

TODO
----

As of March 28, 2017 I intend to elaborate

 * multiple partials configuration to be selected according to frequency
 * interpolation of partial shape between neighbouring frequency-based configuration

Instrument specification
========================


An instrument can have one or more than one sound generator. The sound generator is selected
or interpolated on-the-fly depending on the properties of a note, as pitch or stress.

A sound generator always consists of at least one sympartial.

Sympartial specification
------------------------

The syntax is not (yet?) XML. While developping, I prefer a concise and custom one.

A sympartial is a partial that may be accompanied by further partials implied by
modulation. There is support for frequency modulation, amplitude modulation, and wave shaping.

Sympartial definitions have an integer factor of the base frequency, a deviation in cent (+/-),
and a share of volume. These values are specified as: F+D@S.

A sympartial has an A(D)SR envelope that consists of three bezier shapes.

    * Attack: Length of this phase is always fixed.

    * Sustain: Phase is cropped or extended depending on how long the tone is.
      Extension considers the rise between the last two coordinates.

    * Release: Length and vertical start (maximum) is adjusted to the end of sustain.
      Length is not considered part of the tone length, so it often overlaps with
      the following tones.

Percussive sympartials only have an attack phase that ends by zero. With undefined sustain,
a partial is lengthened with a constant sustain if needed.

Every phase is specified by length (seconds), share at start, than the shares of consecutive
points up to the end. The x-dimension of these points is automatically normalized to the length
of the shape, so only the ratios of the x-positions count. The amplitude value (right of
the comma) is normalized to the start value = 1. If the start value is 0 or omitted at all,
the amplitude values are normalized to the maximum value of the shape.
 
### Example:

    1.2:100;1,50;3,0

In this example, the rise is not linear, but is falling in a decreasing extent. From -50 of -100dB
in the first 0.4 sec, that is slowly reduced to -25 of -100dB in the last.

### Modulations

 - `5;1:100+45` = 5Hz, sine-modulated part relates to constant part in a ratio of 1:100,
   phase angle 45 degrees.

 - `5p;...` 5 times the period

 - ...,env:... - shape (s.a.), but without length and colon. Example: "5;1:100,env:0;1,1;2,0":
   modulation is ratio 1:100 in the middle of the tone, but 0:100 i.e. no modulation at the
   beginning and at the end.

Define modulations by: AM(...) for amplitude modulation, FM(...) for frequency modulation.

### Waveshaping

WS(&lt;shape definition&gt;)

The start of the shape should be at 0, and therefore can be omitted. That shape is reflected
vertically and horizontally so the whole wave period remains symmetric.

## Full syntax

    F+D@S A(...) S(...) R(...) FM(...) AM(...) WS(...)

The clauses are space-separated and can occur in any order. Only the attack is mandatory.



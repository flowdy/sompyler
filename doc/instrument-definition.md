Instrument specification
========================


An instrument can have one or more than one sound generator. The sound generator is selected
or interpolated on-the-fly depending on the properties of a note, as pitch or stress.

A sound generator always consists of at least one sympartial.

Sympartial specification
------------------------

A sympartial is a partial, an elementary tone with a single frequency, that may be
accompanied by further partials implied by modulation. You can define frequency
modulation, amplitude modulation, and wave shape.

A sympartial has an A(D)SR envelope that consists of three bézier shapes.

  * Attack: Length of this phase is always fixed.

  * Sustain: Phase is cropped or extended depending on how long the tone is.
    Extension considers the rise between the last two coordinates.

  * Release: Length and vertical start (maximum) is adjusted to the end of sustain.
    Length of the release phase is not considered part of the defining tone length,
    so tones can overlap.

Percussive sympartials only have an attack phase that ends by zero. With undefined sustain,
a partial is extended by a constant sustain if attack and release cannot fill the required
length alone. A sustain ending by zero conflicts with a defined release if any. There is no
special "decay" phase. Shape attack or sustain/release appropriately. A decay is defined in
attack or sustain or in both, depending on how much of it must be independent from requested
tone length.

Every phase is specified by length (seconds), share at start, than the shares of consecutive
points up to the end, defined by semicolon-separated "x,y"-coordinates describing the polygonic
envelope of the bézier curve. The x-dimension of these points is automatically normalized to
the length of the shape, so only the ratios of the x-positions count. The y-part value is
normalized to the start value = 1. If the start value is 0 or omitted at all, the amplitude
values are normalized to the maximum value of the shape.
 
### Example:

    1.2:100;1,50;3,0

In this example, the rise is not linear, but is falling in a decreasing extent. From -50 of -100dB
in the first 0.4 sec, that is slowly reduced to -25 of -100dB in the last.

### Modulations

 - `5;1:100+45` = 5Hz, sine-modulated part relates to constant part in a ratio of 1:100,
   phase angle 45 degrees.

 - `5p;...` 5 times the carrier period

The tag for frequency modulation is "FM", the tag for amplitude modulation is "AM".

### Waveshaping

You can define the wave shape the same way as you define attack etc., but omit the length.

The shape you define is actually the increasing flank of the result wave. Actually, the y-parts
of the rendered form points are mapped to the x-parts of rendered the wave shape, and the values
get replaced by the corresponding y-values of the wave shape.

Please specify a start value, and the first coordinate with x=0.
A coordinate with y equal to start value will be mapped to the middle line of the wave.

That shape is reflected vertically so the whole wave period remains symmetric.

The sharper the edges are in the curve, the more dominance will get the higher overtones
compared to the lower.


Character definition
--------------------

The essential part of an instrument definition is its "character" that determines how it actually
sounds. In its most complex form, it can adapt to every aspect of a note. Have a glance at
`instruments/dev/piano.spli` for an intermediate level.

There are two or three mandatory properties of the character to define at least. "name" and "source"
are merely informational:

    name: My first instrument
    source: None, really. Just testing.
    character:
        O: sine     # one of "sine", "square", "sawtooth" or "noise"
        A: ...      # attack shape definition, see above
        R: ...      # define release phase if attack ends in ...,n with n>0

With that, you just defined an instrument emitting exactly one frequency.

Properties "S", "AM", "FM", and "WS" are optional. Define a modulation with "np;...", given n≤1,
to get overtones.

Such a simple instrument can easily be developped using `scripts/render-single-sound`.

Do you want more control, richer sound? Be welcome and enhance your pleasure with SPREAD,
PROFILE and TIMBRE.


### PROFILE

Array of property groups.

Lacking properties are completed by using the corresponding property of the base level.

    character:
        O: sine
        R: ... # used for all partials without release definition
        PROFILE:
            - A: ... # fundamental tone, attack definition
              V: 100 # mandatory volume of fundamental
              # R: (omitted)
            - A: ... # 1st overtone
              V: 89
            - ...    # how many partials you like
            

An additional *mandatory* property for volume: "V". The unit is dB. You should stick
to the range 0-100. 100dB represent the maximum volume of the audio system playing back.
It is merely relative and depends on settings on operating system and user-land level.

PROFILE can be an array of integers. As such, the integers indicate the volumes. All
other properties are inherited from above levels of the character definition.


### TIMBRE

Just another shape definition. The x-axis of the shape is mapped to the partial frequency.
The y-axis indicates the factors which multiply (or rather reduce, because they are ≤1) the
PROFILE volumes for the corresponding partials depending on their actual frequency.

To view the graph of a timbre, just use `scripts/render-single-sound -S "20000:..."`.
Make sure, optional dependency `matplotlib` is installed, because the timbre is not a sound
you can listen too, it is rather a function with a custom shape.

Coordinates are not edges by default. Edges in the curve can be defined by an '!' after the
x,y notation. (This is a general feature, not restricted to features. Feel free to try it
for envelope shapes.)


### SPREAD

Array of partial frequency distances in cent unit. A cent unit is 1/1200 of an octave.

Please note that every value implicitly stacks onto the preceding values, and the array is
cropped or extended by zeroes depending on PROFILE length.

### Labels and reference

If a non-property key is given among properties, it is expected to be the label of a property
group. The key must be a string other than the specially handled that have been described
earlier. A labelled property group can only contain sympartial properties.

Wherever you can set a property value, it can be "inherited" indirectly from the property group
the label of which is expected after the distinctive "@" sign. The relationship to the referenced
property group must be sibling of current or of an upper level. Circular references are
detected.

Modulation definitions can have label references, too. The oscillator of the referenced
property group (or "protopartial" if you prefer) is used for the wave form of the modulation.


### Variations

To shape a sound depending on the requested pitch of the tone, you can define a timbre. So you
have a smooth gradual change of partial volume shares. But you cannot define changes to e.g.
attack in this way.

To do that, use variations instead. Just add ATTR and TYPE properties to your
definition, and further properties the keys of which must be either an integer, a float or a
string with a preceding "=" sign, so they can be distinguished from labels.

As a value of such a property ("variation"), you can define all sympartial properties, TIMBRE,
PROFILE, and nested variations as well. Last but not least, you can define new and redefine
existing labelled property groups from hierarchy above. SPREAD is generally not a good idea
to use in variations, though. Chords would contain beats if component tones use different
SPREADs.

ATTR must name a note property that is evaluated to choose the variation:
"pitch" | "stress" | "length" or any custom ones.

TYPE must be set to one of the following values:

  * "merge" – keys of given variations are edges between which is interpolated in a linear
    fashion. Say, you define variations for pitches 400Hz and 800Hz, then a given request
    of pitch 600Hz would lead to an equal interpolation in the middle between these values.

  * "stack" – matching variations add up their properties. Where properties have been defined
    according their keys, replacement takes place.

  * "first" – the first matching variation is selected.

By using variations, you should be able to approach the sounding character of physical
instruments in any extent of detail you might wish. For instance, the keys of a piano all
have their distinct sounding beside the pitch. Just compare A0 and C8, i.e. the left- and
the rightmost key. The right one is much shorter and more percussive than the left.

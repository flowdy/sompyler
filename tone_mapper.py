import yaml
import codecs
from sound_generator import Shape

TOTAL_KEYS_NUM = 88

def get_mapper_from(source_file):

    def tone_to_frequence(base_freq, substract, denominator):
        base_freq = float(base_freq)
        substract = int(substract)
        denominator = float(denominator)
        return lambda n: base_freq * 2 ** ((n-substract)/denominator)
    
    def get_mapping (mapper, num):
        freqmap = [None]

        for n in range(num):
            freq = mapper(n+1)
            freqmap.append(freq)
            for name in i.split():                      
                tone_names_to_freq_map[name] = freq

        return freqmap

    with codecs.open(source_file, encoding="utf-8") as tones:
        scale = re.match(
            r'^# SOMPYLER TONE SCALE: (\d+)D(\d+)/(\d+)',
            next(tones)
        )
        if not scale: raise Exception(
           "{} not recognized as a sompyler tone scale".format(source_file)
           + """
             Prepend it with following line:
             SOMPYLER TONE SCALE: 440D49/12
             The values can be differenct, to adapt for other cultures.
             See documentation to learn what they mean.
             """
        )
        base_freq = int(scale.group(1))
        octave_intervals = int(scale.group(3))
        std_freqmap = get_mapping(
            tone_to_frequence(*scale.groups), TOTAL_KEYS_NUM
        )
        tone_names_to_num_map = {
            (name, num) for names.split(" ") for num, names in tones
        }
        
    def get_cache (deviant_base_freq=None, *tuning):

        if not ( deviant_base_freq and deviant_base_freq == base_freq ):
            freqmap = get_mapping( tone_to_frequence(
                deviant_base_freq, *scale[1:]
            ), TOTAL_KEYS_NUM) 
            tuner = Shape(TOTAL_KEYS_NUM, tuning).render()
            for i, freq in enumerate(freqmap):
                freqmap[i] += freq * 2 ** (
                    tuner[i] / (octave_intervals * 100.0)
                )

        else: freqmap = std_freqmap

        return lambda n: (
            freqmap[ n if isinstance(n,int) else tone_names_to_num_map[n] ]
        )

    return get_cache


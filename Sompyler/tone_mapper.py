import yaml
import codecs
import re

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

        return freqmap

    tone_names_to_num_map = {}

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
             The values can be difference, to adapt for other cultures.
             See documentation to learn what they mean.
             """
        )
        base_freq = float(scale.group(1))
        substract = int(scale.group(2))
        octave_intervals = int(scale.group(3))
        std_freqmap = get_mapping(
            tone_to_frequence(*scale.groups()), TOTAL_KEYS_NUM
        )
        for num, names in enumerate(tones):
            for name in names.strip().split(" "):
                tone_names_to_num_map[name] = num+1 
        
    def get_cache (deviant_base_freq=base_freq, *tuning):

        if tuning:
            offset = tuning[0]
            tunes = [ i*100+c for i, c in enumerate(tuning[1:]) ]
            tune0 = tunes[ -offset % octave_intervals ]
            modop = octave_intervals * 100
            for n in range(TOTAL_KEYS_NUM):
                i = (n - offset) % octave_intervals
                freqmap[n] = deviant_base_freq * 2 ** (
                    ( int( (n-substract) / octave_intervals ) * modop
                      + ( tunes[i] - tune0 ) % modop
                    ) / modop
                )
            
        elif not ( deviant_base_freq == base_freq ):
            freqmap = get_mapping( tone_to_frequence(
                deviant_base_freq, *scale[1:]
            ), TOTAL_KEYS_NUM) 

        else: freqmap = std_freqmap
        
        return lambda n: (
            freqmap[ n if isinstance(n,int) else tone_names_to_num_map[n] ]
        )

    return get_cache


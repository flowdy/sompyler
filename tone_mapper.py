import yaml
import codecs

def get_mapper_from(yaml_source_file):

    with codecs.open(yaml_source_file, encoding="utf-8") as tones:
        tones_dir = yaml.safe_load(tones)
    
    def tone_mapper(base_freq, denominator, substract):
        base_freq = float(base_freq)
        denominator = float(denominator)
        substract = int(substract)
        return lambda n: base_freq * 2 ** ((n-substract)/denominator)
    
    mapper = tone_mapper(*tones_dir[0].split(" "))

    tone_names_to_freq_map = {}

    for n, i in enumerate(tones_dir[1:]):
        freq = mapper(n+1)
        for name in i.split():                      
            tone_names_to_freq_map[name] = freq
        tones_dir[n+1] = freq

    tones_dir[0] == None

    return lambda n: (
        tones_dir[n] if type(n) == int else tone_names_to_freq_map[n]
    )

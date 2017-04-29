from sound_generator import Shape

s1 = Shape.from_string(".16:1,73;2,100")
print s1.coords
s2 = Shape.from_string(".48:1,86;2,99;3,98;4,99;5,100")
print s2.coords
for i in 0.2, 0.4, 0.6, 0.8:
    s3 = s1.weighted_avg_with(i, s2)
    print i, ":", s3.coords

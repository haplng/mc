# the seven bots of a round must not share a name: draw the names 300 times
import sys; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
from collections import Counter
seen = Counter(); twice = 0
for k in range(300):
    c('function bw:ai/names'); ns = [c(f'data get storage bw:ai n{i}').split(': ')[-1].strip('"') for i in range(1, 8)]
    twice += len(set(ns)) != 7; seen.update(ns)
print('draws with a name twice:', twice, '| names used', len(seen), '| least and most often', min(seen.values()), max(seen.values()))

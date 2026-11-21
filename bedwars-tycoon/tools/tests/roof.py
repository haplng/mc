# who climbs onto the roof of a base, and how: keeps the last seconds of every bot and prints them when one stands high above the floor
import sys, time, pickle, math, re, json; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
stage = int(sys.argv[1]); mid = sys.argv[2]; dur = int(sys.argv[3]); high = float(sys.argv[4]) if len(sys.argv) > 4 else 69.5
c('function bw:game/close'); time.sleep(1)
b = join(); c(f'scoreboard players set tester bw.stage {stage}')
print(mid, 'stage', stage, 'start', start(mid, b)); time.sleep(0.5); c('gamemode spectator tester')
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
hist = {i: [] for i in range(1, 8)}; t0 = time.time(); dumps = 0; quiet = {}
while time.time() - t0 < dur and dumps < 4:
    for i in range(1, 8):
        a = c(f'execute as {B(i)} run data get entity @s Pos')
        m = re.search(r'\[(-?[\d.]+)d, (-?[\d.]+)d, (-?[\d.]+)d\]', a)
        if not m: hist[i].append((round(time.time() - t0, 1), 'dead')); continue
        p = tuple(round(float(v), 1) for v in m.groups())
        g = pos(f'@e[type=marker,tag=bw.g{i},limit=1]')
        hist[i].append((round(time.time() - t0, 1), p, 'st', sc(B(i), 'bw.st'), 'dest', sc(B(i), 'bw.dest'), 'goal', g and tuple(round(v, 1) for v in g), 'jc', sc(B(i), 'bw.jc'), 'av', sc(B(i), 'bw.av'), 'ft', sc(B(i), 'bw.ft')))
        hist[i] = hist[i][-40:]
        if p[1] >= high and quiet.get(i, 0) < time.time():
            print(f'--- bot{i} is up at {p}:'); [print('   ', h) for h in hist[i]]; dumps += 1; quiet[i] = time.time() + 60
    time.sleep(0.15)
print('done', round(time.time() - t0)); b.close()

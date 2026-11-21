# one bot put at a spot with a goal (and, optionally, a trail of its own steps to go back along); prints where it goes
import sys, time, re, math, json; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
mid, stage, team = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); bx, by, bz = map(float, sys.argv[4:7]); route = json.loads(sys.argv[7]); trail = json.loads(sys.argv[8]) if len(sys.argv) > 8 else []
secs = float(sys.argv[9]) if len(sys.argv) > 9 else 12
c('tick unfreeze'); c('function bw:game/close'); time.sleep(1)
b = join(); c(f'scoreboard players set tester bw.stage {stage}')
print('start', start(mid, b)); time.sleep(0.5); c('gamemode spectator tester'); time.sleep(3)
B = f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={team}}},limit=1]'
L = lambda pts: '[' + ','.join(f'[{x}d,{y}d,{z}d]' for x, y, z in pts) + ']'
c(f'data modify storage bw:bot r{team} set value {L(route)}'); c(f'data modify storage bw:bot tr{team} set value {L(trail)}')
gx, gy, gz = route[0]; c(f'tp @e[type=marker,tag=bw.g{team},limit=1] {gx} {gy} {gz}')
for o, v in (('bw.st', 2), ('bw.dest', 1), ('bw.calm', 4000), ('bw.av', 0), ('bw.avn', 25), ('bw.stuck', 0), ('bw.wpt', 0), ('bw.off', 0), ('bw.avf', 0)): c(f'scoreboard players set {B} {o} {v}')
c(f'tp {B} {bx} {by} {bz}'); c(f'tp tester {bx} {by + 8} {bz}')
t0 = time.time(); last = None
while time.time() - t0 < secs:
    p = pos(B); g = pos(f'@e[type=marker,tag=bw.g{team},limit=1]')
    line_ = (p, 'goal', g, *[f'{o[3:]} {sc(B, o)}' for o in ('bw.st', 'bw.av', 'bw.avn', 'bw.avf', 'bw.stuck', 'bw.off', 'bw.wpt')], 'r', c(f'data get storage bw:bot r{team}').count('[') - 1, 'tr', c(f'data get storage bw:bot tr{team}').count('[') - 1)
    if line_ != last: print(round(time.time() - t0, 1), *line_)
    last = line_
    if sc(B, 'bw.st') != 2: print('   state changed: arrived or something else'); break
    time.sleep(0.25)
b.close()

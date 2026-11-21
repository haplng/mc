# one bot put at a given spot with a given goal, the server stepped tick by tick
import sys, time, re, math; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
mid, stage = sys.argv[1], int(sys.argv[2]); bx, by, bz = map(float, sys.argv[3:6]); gx, gy, gz = map(float, sys.argv[6:9]); n = int(sys.argv[9]) if len(sys.argv) > 9 else 40
c('tick unfreeze'); c('function bw:game/close'); time.sleep(1)
b = join(); c(f'scoreboard players set tester bw.stage {stage}')
print('start', start(mid, b)); time.sleep(0.5); c('gamemode spectator tester'); time.sleep(3)
B = '@e[type=mannequin,tag=bw.bot,scores={bw.team=1},limit=1]'
c(f'data modify storage bw:bot r1 set value [[{gx}d,{gy}d,{gz}d]]'); c('data modify storage bw:bot tr1 set value []')
c(f'tp @e[type=marker,tag=bw.g1,limit=1] {gx} {gy} {gz}')
for o, v in (('bw.st', 2), ('bw.dest', 1), ('bw.calm', 2000), ('bw.av', 0), ('bw.avn', 25), ('bw.stuck', 0), ('bw.wpt', 0), ('bw.off', 0)): c(f'scoreboard players set {B} {o} {v}')
c(f'tp {B} {bx} {by} {bz}'); c(f'tp tester {bx} {by + 6} {bz}')
c('tick freeze')
def blk(x, y, z):
    return '.' if 'passed' in c(f'execute if block {x} {y} {z} #bw:open') else '#'
fx, fy, fz = math.floor(bx), math.floor(by), math.floor(bz)
for y in (fy + 2, fy + 1, fy, fy - 1):
    print('y', y)
    for z in range(fz - 3, fz + 4): print(f'   z{z:4d} ' + ''.join(blk(x, y, z) for x in range(fx - 3, fx + 5)))
for k in range(n):
    c('tick step 1'); time.sleep(0.08)
    p = c(f'data get entity {B} Pos'); m = re.search(r'\[(-?[\d.]+)d, (-?[\d.]+)d, (-?[\d.]+)d\]', p)
    rot = re.findall(r'-?[\d.]+', c(f'data get entity {B} Rotation').split('data:')[-1])[:2]
    print(k, tuple(round(float(v), 2) for v in m.groups()) if m else None, 'rot', [round(float(v)) for v in rot], *[f'{o[3:]} {sc(B, o)}' for o in ('bw.mf', 'bw.ms', 'bw.av', 'bw.avs', 'bw.avn', 'bw.stuck', 'bw.jc', 'bw.br', 'bw.st', 'bw.off')], 'high', sc('#high'), 'drop', sc('#drop'))
c('tick unfreeze'); b.close()

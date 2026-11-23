# Stasis: falling into the void, the player hangs for three seconds
import sys, time, re, math, struct; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0')
print('start', start('tea', b), 'state', sc('#state')); time.sleep(1)
c('scoreboard players set tester bw.h_stasis 1'); c('execute as tester run function bw:hack/apply'); c('effect give tester minecraft:resistance infinite 4 true')
is_ = lambda x, y, z, blk: 'passed' in c(f'execute if block {x} {y} {z} {blk}')
# a column of nothing next to the red island
p0 = pos('tester'); X = Z = None
for dx, dz in ((14, 0), (-14, 0), (0, 14), (0, -14), (18, 0), (0, 18), (0, -18), (-18, 0)):
    x, z = math.floor(p0[0]) + dx, math.floor(p0[2]) + dz
    if 'passed' in c(f'execute unless blocks {x} 40 {z} {x} 100 {z} {x} 40 {z + 1} masked') and all(is_(x, y, z, 'minecraft:air') for y in range(60, 96, 5)): X, Z = x, z; break
print('void column at', X, Z, 'from', p0)
def fall(y0, n, step=0.9):
    y = y0
    for k in range(n):
        y -= step; b._send('play', 'move_player_pos', struct.pack('>dddb', X + 0.5, y, Z + 0.5, 0)); b._send('play', 'client_tick_end'); time.sleep(0.11)
    return y
grav = lambda: c('attribute tester minecraft:gravity base get').split()[-1]
c(f'tp tester {X + 0.5} 95 {Z + 0.5}'); time.sleep(0.6); b.tplog = []
y = fall(95, 2); print('falling 1.8 blocks: stc', sc('tester', 'bw.stc'), 'gravity', grav(), 'fall distance ok?', c('execute as tester if predicate bw:falling')[:11])
y = fall(y, 3); time.sleep(0.15)
print('falling 4.5 blocks: stc', sc('tester', 'bw.stc'), 'gravity', grav(), 'server y', pos('tester')[1], 'teleports (flags, vy, y):', [(hex(f), v, yy) for f, v, yy in b.tplog])
time.sleep(1.5); print('  1.5 s later: stc', sc('tester', 'bw.stc'), 'gravity', grav())
time.sleep(1.8); print('  3.3 s later: stc', sc('tester', 'bw.stc'), 'gravity', grav())
# again, but this time a block appears under the feet after a second
c('scoreboard players set tester bw.stc 0'); c(f'tp tester {X + 0.5} 95 {Z + 0.5}'); time.sleep(0.6); y = fall(95, 5); time.sleep(0.2)
py = pos('tester')[1]; print('second fall: stc', sc('tester', 'bw.stc'), 'gravity', grav(), 'y', py)
c(f'setblock {X} {math.floor(py) - 1} {Z} minecraft:white_wool'); c(f'tp tester {X + 0.5} {math.floor(py)} {Z + 0.5}'); time.sleep(0.5)
print('  a block under the feet: stc', sc('tester', 'bw.stc'), 'gravity', grav())
c(f'setblock {X} {math.floor(py) - 1} {Z} minecraft:air')
print(errors()[-300:]); c('function bw:game/close'); time.sleep(1); print('after the round: gravity', grav()); b.close()

# a lost bot: put at a spot with something to do, told it cannot get on; prints the way home it works out and how the walk goes
import sys, time, re, math, json; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
mid, stage, team = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); bx, by, bz = map(float, sys.argv[4:7]); to = sys.argv[7]; dest = int(sys.argv[8]); secs = float(sys.argv[9]) if len(sys.argv) > 9 else 25
setup = sys.argv[10] if len(sys.argv) > 10 else ''
c('tick unfreeze'); c('function bw:game/close'); time.sleep(1)
b = join(); c(f'scoreboard players set tester bw.stage {stage}')
print('start', start(mid, b)); time.sleep(0.5); c('gamemode spectator tester'); time.sleep(3); c('scoreboard players set #dbg bw 1')
B = f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={team}}},limit=1]'
for cmd in [x for x in setup.split(';') if x.strip()]: c(cmd)
c(f'data modify storage bw:bot to{team} set value "{to}"'); c(f'scoreboard players set {B} bw.dest {dest}')
for o, v in (('bw.st', 2), ('bw.calm', 4000), ('bw.av', 0), ('bw.avn', 25), ('bw.stuck', 0), ('bw.wpt', 0), ('bw.off', 0), ('bw.avf', 0), ('bw.rrc', 0)): c(f'scoreboard players set {B} {o} {v}')
c(f'tp {B} {bx} {by} {bz}'); c(f'tp tester {bx} {by + 8} {bz}'); time.sleep(0.4)
n0 = len(b.chat); c(f'execute as {B} run function bw:ai/reroute'); time.sleep(0.3)
r = c(f'data get storage bw:bot r{team}'); pts = re.findall(r'\[(-?[\d.]+)d, (-?[\d.]+)d, (-?[\d.]+)d\]', r)
print('after reroute: dest', sc(B, 'bw.dest'), 'to', c(f'data get storage bw:bot to{team}')[-6:], 'kept', c(f'data get storage bw:bot ho{team}')[-30:], '| way has', len(pts), 'points:', ' '.join(f'({float(x):g},{float(y):g},{float(z):g})' for x, y, z in pts[:6]), '...', ' '.join(f'({float(x):g},{float(y):g},{float(z):g})' for x, y, z in pts[-3:]))
print('  ', [m[:160] for m in b.chat[n0:]])
t0 = time.time(); last = None; seen = len(b.chat)
while time.time() - t0 < secs:
    p = pos(B); n = c(f'data get storage bw:bot r{team}').count('[') - 1
    line_ = (p and tuple(round(v, 1) for v in p), 'left', n, 'st', sc(B, 'bw.st'), 'dest', sc(B, 'bw.dest'), 'stuck', sc(B, 'bw.stuck'), 'rrc', sc(B, 'bw.rrc'))
    if line_ != last and (last is None or abs(n - last[2]) >= 4 or line_[3:] != last[3:]): print(round(time.time() - t0, 1), *line_); last = line_
    for m in b.chat[seen:]:
        if m.startswith(('HOMED', 'REROUTE', 'GIVEUP')): print('   ', m[:170])
    seen = len(b.chat)
    if any(m.startswith('HOMED') for m in b.chat[n0:]): 
        time.sleep(0.5); print('   then: st', sc(B, 'bw.st'), 'dest', sc(B, 'bw.dest'), 'at', c(f'data get storage bw:bot at{team}')[-6:], 'to', c(f'data get storage bw:bot to{team}')[-6:], 'pos', pos(B)); break
    time.sleep(0.25)
print(errors()[-300:]); b.close()

# the last seconds before a bot loses its way: positions, goal, route - printed at the first REROUTE-OFF
import sys, time, pickle, math, re, json; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
stage = int(sys.argv[1]); mid = sys.argv[2]; dur = int(sys.argv[3]); want = sys.argv[4] if len(sys.argv) > 4 else 'REROUTE-OFF'
c('tick unfreeze'); c('function bw:game/close'); time.sleep(1)
b = join(); c(f'scoreboard players set tester bw.stage {stage}')
print(mid, 'stage', stage, 'start', start(mid, b)); time.sleep(0.5); c('gamemode spectator tester'); c('scoreboard players set #dbg bw 1')
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
hist = {i: [] for i in range(1, 8)}; t0 = time.time(); seen = 0
def snap(i):
    p = pos(B(i)); g = pos(f'@e[type=marker,tag=bw.g{i},limit=1]')
    return (round(time.time() - t0, 1), p and tuple(round(v, 1) for v in p), g and tuple(round(v, 1) for v in g), sc(B(i), 'bw.st'), sc(B(i), 'bw.dest'), sc(B(i), 'bw.br'), sc(B(i), 'bw.av'), sc(B(i), 'bw.stuck'),
            c(f'data get storage bw:bot r{i}').count('[') - 1, c(f'data get storage bw:bot tr{i}').count('[') - 1, c(f'data get storage bw:bot at{i}')[-5:], c(f'data get storage bw:bot to{i}')[-5:])
while time.time() - t0 < dur and sc('#state') == 3:
    for i in range(1, 8):
        hist[i].append(snap(i)); hist[i] = hist[i][-60:]
    hit = None
    for mm in b.chat[seen:]:
        if mm.startswith(want + ' '): hit = mm; break
    seen = len(b.chat)
    if hit:
        c('tick freeze'); i = int(re.search(r'bot(\d)', hit).group(1)); print(hit[:220])
        print('route left:', c(f'data get storage bw:bot r{i}')[30:600]); print('kept:', c(f'data get storage bw:bot ho{i}')[-60:])
        last = None
        for h in hist[i]:
            if last is None or h[1:] != last[1:]: print('  ', *h)
            last = h
        if len(sys.argv) > 5:
            x0, x1, z0, z1, y0, y1 = (int(v) for v in sys.argv[5].split(','))
            for z in range(z0, z1 + 1):
                for y in range(y1, y0 - 1, -1):
                    row = ''
                    for x in range(x0, x1 + 1):
                        if 'passed' in c(f'execute if block {x} {y} {z} #bw:open'): row += '.'
                        else:
                            a_ = c(f'execute positioned {x} {y} {z} if predicate bw:built'); pl = c(f'execute positioned {x} {y} {z} if predicate bw:placed')
                            row += 'B' if 'passed' in a_ else 'P' if 'passed' in pl else 'W' if 'passed' in c(f'execute if block {x} {y} {z} #minecraft:wool') else '#'
                    print(f'   z{z} y{y}: {row}')
        break
    time.sleep(0.15)
c('tick unfreeze'); c('function bw:game/close'); b.close()

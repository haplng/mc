# how a bot gets stuck: keeps the last seconds of every bot and prints them when its 'stuck' counter runs high
import sys, time, pickle, math, re, json; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
stage = int(sys.argv[1]); mid = sys.argv[2]; dur = int(sys.argv[3]); lim = int(sys.argv[4]) if len(sys.argv) > 4 else 150
c('function bw:game/close'); time.sleep(1)
b = join(); c(f'scoreboard players set tester bw.stage {stage}')
print(mid, 'stage', stage, 'start', start(mid, b)); time.sleep(0.5); c('gamemode spectator tester')
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
hist = {i: [] for i in range(1, 8)}; t0 = time.time(); dumps = 0; quiet = {}
while time.time() - t0 < dur and dumps < 3:
    for i in range(1, 8):
        a = c(f'execute as {B(i)} run data get entity @s Pos')
        m = re.search(r'\[(-?[\d.]+)d, (-?[\d.]+)d, (-?[\d.]+)d\]', a)
        if not m: hist[i].append((round(time.time() - t0, 1), 'dead')); continue
        p = tuple(round(float(v), 1) for v in m.groups())
        g = pos(f'@e[type=marker,tag=bw.g{i},limit=1]'); stuck = sc(B(i), 'bw.stuck')
        rl = c(f'data get storage bw:bot r{i}'); tl = c(f'data get storage bw:bot tr{i}')
        hist[i].append((round(time.time() - t0, 1), p, 'st', sc(B(i), 'bw.st'), 'dest', sc(B(i), 'bw.dest'), 'goal', g and tuple(round(v, 1) for v in g), 'stuck', stuck, 'av', sc(B(i), 'bw.av'), 'avn', sc(B(i), 'bw.avn'), 'wpt', sc(B(i), 'bw.wpt'),
                        'r', rl.count('['), 'tr', tl.count('['), c(f'data get storage bw:bot at{i}')[-5:], c(f'data get storage bw:bot to{i}')[-5:]))
        hist[i] = hist[i][-70:]
        if stuck is not None and stuck >= lim and quiet.get(i, 0) < time.time():
            print(f'--- bot{i} is stuck at {p}:'); [print('   ', h) for h in hist[i][-6:]]; dumps += 1; quiet[i] = time.time() + 60
            c('tick freeze')
            cv = pickle.load(open(f'/tmp/bwout/canvas/{mid}.pkl', 'rb'))['b']; mp = {m_['id']: m_ for m_ in json.load(open('/tmp/bwout/maps.json'))}; cx, cy, cz = mp[mid]['center']
            fx, fy, fz = math.floor(p[0]), math.floor(p[1] + 0.01), math.floor(p[2])
            for y in (fy + 2, fy + 1, fy, fy - 1):
                rows = []
                for z in range(fz - 3, fz + 4):
                    row = ''
                    for x in range(fx - 3, fx + 4):
                        o = 'passed' in c(f'execute if block {x} {y} {z} #bw:open'); s_ = cv.get((x - cx, y - cy, z - cz))
                        row += '@' if (x, z) == (fx, fz) and y in (fy, fy + 1) and o else ('.' if o and not s_ else 'o' if o else (s_.replace('minecraft:', '')[0] if s_ else '#'))
                    rows.append(row)
                print(f'   y{y}: ' + ' '.join(rows))
            for k in range(14):
                c('tick step 1'); time.sleep(0.08)
                pp = pos(B(i)); rot = re.findall(r'-?[\d.]+', c(f'data get entity {B(i)} Rotation').split('data:')[-1])[:2]
                print('     ', k, pp, 'rot', [round(float(v)) for v in rot], *[f'{o[3:]} {sc(B(i), o)}' for o in ('bw.mf', 'bw.ms', 'bw.av', 'bw.avs', 'bw.avn', 'bw.stuck', 'bw.jc', 'bw.br', 'bw.mine', 'bw.off')], 'high', sc('#high'), 'drop', sc('#drop'))
            c('tick unfreeze')
    time.sleep(0.1)
print('done', round(time.time() - t0)); b.close()

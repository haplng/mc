import sys, time, pickle, math, re; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
stage = int(sys.argv[1]); mid = sys.argv[2]; dur = int(sys.argv[3])
cv = pickle.load(open(f'/tmp/bwout/canvas/{mid}.pkl', 'rb'))['b']
maps = {m['id']: m for m in json.load(open('/tmp/bwout/maps.json'))}; cx, cy, cz = maps[mid]['center']
c('function bw:game/close'); time.sleep(1)
b = join(); c(f'scoreboard players set tester bw.stage {stage}')
print(mid, 'stage', stage, 'start', start(mid, b)); time.sleep(0.5); c('gamemode spectator tester')
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
def dump(i):
    p = pos(B(i)); g = pos(f'@e[type=marker,tag=bw.g{i},limit=1]')
    print(f'bot{i} pos {p} goal {g} st {sc(B(i), "bw.st")} pst {sc(B(i), "bw.pst")} dest {sc(B(i), "bw.dest")} mf {sc(B(i), "bw.mf")} br {sc(B(i), "bw.br")} mine {sc(B(i), "bw.mine")} stuck {sc(B(i), "bw.stuck")} jc {sc(B(i), "bw.jc")} t1 {sc(B(i), "bw.t1")} tool {sc(B(i), "bw.tool")} ground {c(f"execute as {B(i)} if predicate bw:ground")[:11]} rot {c(f"data get entity {B(i)} Rotation")[-18:]}')
    print('   at', c(f'data get storage bw:bot at{i}')[-5:], 'to', c(f'data get storage bw:bot to{i}')[-5:], 'route', c(f'data get storage bw:bot r{i}')[38:200], '| foe near', c(f'execute at {B(i)} if entity @e[tag=bw.fighter,distance=0.1..16]')[:22])
    bx, by, bz = math.floor(p[0]), math.floor(p[1] + 0.01), math.floor(p[2])
    for y in (by + 2, by + 1, by, by - 1, by - 2):
        rows = []
        for z in range(bz - 4, bz + 5):
            row = ''
            for x in range(bx - 4, bx + 5):
                s = cv.get((x - cx, y - cy, z - cz)); o = 'passed' in c(f'execute if block {x} {y} {z} #bw:open')
                gg = g and (x, y, z) == (math.floor(g[0]), math.floor(g[1]), math.floor(g[2]))
                row += ('G' if gg else '@' if (x, z) == (bx, bz) and y in (by, by + 1) else '.' if o and not s else ('o' if o else ((s or '#').replace('minecraft:', '')[0])))
            rows.append(row)
        print(f'   y{y}: ' + ' '.join(rows))
t0 = time.time(); last = {}; still = {}; dumps = 0
while time.time() - t0 < dur and dumps < 3:
    time.sleep(3)
    for i in range(1, 8):
        p = pos(B(i)); st = sc(B(i), 'bw.st')
        if not p: still[i] = 0; continue
        if i in last and abs(p[0] - last[i][0]) + abs(p[2] - last[i][2]) < 1.0 and st in (2, 4, 0): still[i] = still.get(i, 0) + 3
        else: still[i] = 0
        last[i] = p
        if still[i] >= 15 and dumps < 3: print(f'[{time.time() - t0:.0f}s] not moving for {still[i]}s:'); dump(i); dumps += 1; still[i] = -30
print('done', round(time.time() - t0)); b.close()

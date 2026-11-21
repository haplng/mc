import sys, time, pickle, math, re; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
stage = int(sys.argv[1]); mid = sys.argv[2]; dur = int(sys.argv[3])
cv = pickle.load(open(f'/tmp/bwout/canvas/{mid}.pkl', 'rb'))['b']
maps = {m['id']: m for m in json.load(open('/tmp/bwout/maps.json'))}; cx, cy, cz = maps[mid]['center']
c('function bw:game/close'); time.sleep(1)
b = join(); c(f'scoreboard players set tester bw.stage {stage}')
print(mid, 'stage', stage, 'start', start(mid, b)); time.sleep(0.5); c('gamemode spectator tester')
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
t0 = time.time(); dumped = 0; seen = 0; mspt = []; stuck_events = 0; deaths = 0; voids = 0
def dump(i):
    p = pos(B(i)); g = pos(f'@e[type=marker,tag=bw.g{i},limit=1]')
    print(f'  STUCK bot{i} pos {p} goal {g} st {sc(B(i), "bw.st")} dest {sc(B(i), "bw.dest")} br {sc(B(i), "bw.br")} mine {sc(B(i), "bw.mine")} stuck {sc(B(i), "bw.stuck")} at {c(f"data get storage bw:bot at{i}")[-6:]} to {c(f"data get storage bw:bot to{i}")[-6:]} ground {c(f"execute as {B(i)} if predicate bw:ground")[:11]}')
    print('   route', c(f'data get storage bw:bot r{i}')[38:200])
    bx, by, bz = math.floor(p[0]), math.floor(p[1] + 0.01), math.floor(p[2])
    for y in (by + 2, by + 1, by, by - 1):
        rows = []
        for z in range(bz - 3, bz + 4):
            row = ''
            for x in range(bx - 3, bx + 4):
                s = cv.get((x - cx, y - cy, z - cz)); o = 'passed' in c(f'execute if block {x} {y} {z} #bw:open')
                row += ('@' if (x, z) == (bx, bz) and y in (by, by + 1) else '.' if o and not s else ('o' if o else ((s or '#').replace('minecraft:', '')[0].upper())))
            rows.append(row)
        print(f'   y{y}: ' + ' '.join(rows))
while time.time() - t0 < dur and sc('#state') == 3:
    time.sleep(5)
    for i in range(1, 8):
        s = sc(B(i), 'bw.stuck')
        if s is not None and s >= 100:
            stuck_events += 1
            if dumped < 4: dump(i); dumped += 1
    m = re.search(r'Average time per tick: ([\d.]+)', c('tick query'))
    if m: mspt.append(float(m.group(1)))
    for mm in b.chat[seen:]:
        if '처치' in mm or '죽' in mm: deaths += 1
        if '죽었어' in mm or '죽어서' in mm: voids += 1
        if '침대 파괴' in mm or '탈락' in mm: print(f'[{time.time()-t0:4.0f}s]', mm.strip()[:60])
    seen = len(b.chat)
gear = ' '.join(f'{i}:sw{sc(f"#bsw{i}")}a{sc(f"#bar{i}")}t{sc(f"#btl{i}")}' for i in range(1, 8))
print(f'END {mid} sec {sc("#sec")} beds', ''.join(str(sc(f'#bed{i}')) for i in range(8)), 'out', ''.join(str(sc(f'#out{i}')) for i in range(8)), f'deaths {deaths} (no killer {voids}) stuck-samples {stuck_events} mspt avg {sum(mspt) / max(1, len(mspt)):.1f} max {max(mspt or [0])}')
print('  gear', gear, '| upgrades', ' '.join(f'{i}:s{sc(f"#sharp{i}")}p{sc(f"#prot{i}")}f{sc(f"#fl{i}")}' for i in range(1, 8)))
e = errors(); print(e[-600:] if e else ''); b.close()

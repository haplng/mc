# lost bots: every time one works out a way home, whether it gets there, and bots that stand still for long
import sys, time, pickle, math, re, json; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
stage = int(sys.argv[1]); mid = sys.argv[2]; dur = int(sys.argv[3]); maxdump = int(sys.argv[4]) if len(sys.argv) > 4 else 4
cv = pickle.load(open(f'/tmp/bwout/canvas/{mid}.pkl', 'rb'))['b']
maps = {m['id']: m for m in json.load(open('/tmp/bwout/maps.json'))}; cx, cy, cz = maps[mid]['center']
c('function bw:game/close'); time.sleep(1)
b = join(); c(f'scoreboard players set tester bw.stage {stage}')
print(mid, 'stage', stage, 'start', start(mid, b)); time.sleep(0.5); c('gamemode spectator tester'); c('scoreboard players set #dbg bw 1')
for k in ('#reroutes', '#giveups'): c(f'scoreboard players set {k} bw 0')
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
def dump(p, g=None):
    bx, by, bz = math.floor(p[0]), math.floor(p[1] + 0.01), math.floor(p[2])
    for y in (by + 2, by + 1, by, by - 1, by - 2):
        rows = []
        for z in range(bz - 5, bz + 6):
            row = ''
            for x in range(bx - 5, bx + 6):
                s = cv.get((x - cx, y - cy, z - cz)); o = 'passed' in c(f'execute if block {x} {y} {z} #bw:open')
                gg = g and (x, y, z) == (math.floor(g[0]), math.floor(g[1]), math.floor(g[2]))
                row += ('G' if gg else '@' if (x, z) == (bx, bz) and y in (by, by + 1) else '.' if o and not s else ('o' if o else ((s or '#').replace('minecraft:', '')[0])))
            rows.append(row)
        print(f'   y{y}: ' + ' '.join(rows))
t0 = time.time(); seen = 0; cnt = {}; dumped = 0; open_ = {}; took = []; lastpos = {}; still = {}; mspt = []
while time.time() - t0 < dur and sc('#state') == 3:
    time.sleep(2); now = time.time() - t0
    for mm in b.chat[seen:]:
        k = mm.split(' ')[0]
        if k in ('REROUTE', 'REROUTE-HOME', 'REROUTE-OFF', 'GIVEUP', 'HOMED'):
            cnt[k] = cnt.get(k, 0) + 1; bot = re.search(r'bot(\d)', mm).group(1)
            if k == 'HOMED':
                if bot in open_: took.append(round(now - open_.pop(bot)))
                continue
            if k != 'GIVEUP': open_.setdefault(bot, now)
            v = re.findall(r'(-?\d+\.\d+)d', mm)
            if k in ('REROUTE-OFF', 'GIVEUP') or cnt[k] <= 2: print(f'[{now:4.0f}s]', mm[:200])
            if len(v) >= 6 and k in ('REROUTE-OFF', 'GIVEUP') and dumped < maxdump:
                dumped += 1; dump(tuple(float(x) for x in v[:3]), tuple(float(x) for x in v[3:6]))
    seen = len(b.chat)
    for i in range(1, 8):
        p = pos(B(i))
        if p is None: lastpos.pop(i, None); still[i] = 0; continue
        if i in lastpos and math.dist(p, lastpos[i]) < 0.3: still[i] = still.get(i, 0) + 2
        else: still[i] = 0
        lastpos[i] = p
        if still[i] in (40, 80, 160): print(f'[{now:4.0f}s] bot{i} has not moved for {still[i]} s at', p, 'st', sc(B(i), 'bw.st'), 'dest', sc(B(i), 'bw.dest'), 'rrc', sc(B(i), 'bw.rrc'))
    m = re.search(r'Average time per tick: ([\d.]+)', c('tick query'))
    if m: mspt.append(float(m.group(1)))
print('END', mid, 'sec', sc('#sec'), 'reroutes', sc('#reroutes'), cnt, 'gave up', sc('#giveups'), '| seconds from losing the way to being back on it:', sorted(took), '| never got back:', len(open_),
      '| out', ''.join(str(sc(f'#out{i}')) for i in range(8)), f'| mspt avg {sum(mspt) / max(1, len(mspt)):.1f} max {max(mspt or [0])}')
e = errors(); print(e[-400:] if e else ''); c('function bw:game/close'); b.close()

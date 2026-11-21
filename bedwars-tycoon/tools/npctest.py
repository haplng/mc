"""Every shopkeeper is where it should be, exactly once; one that is killed comes back by itself.
Runs against the test server after the pack is installed (uses forceload, so no player is needed)."""
import sys, time, re, json, math
sys.path.insert(0, '/home/claude/mc/tools')
import rcon
r = rcon.Rcon()
ROOT = '/home/claude/bw'
PACK = ROOT + '/out3/bedwars_maps/data/bw/function'
info = [i for i in json.load(open(ROOT + '/out3/maps.json', encoding='utf-8')) if not i.get('empty')]
def npcs(mid):
    out = []
    for l in open(f'{PACK}/step/{mid}/try.mcfunction', encoding='utf-8'):
        m = re.match(r'summon minecraft:villager (\S+) (\S+) (\S+) .*Rotation:\[(\S+?)f,.*Tags:\[(.*?)\]', l)
        if m: out.append((float(m[1]), float(m[2]), float(m[3]), float(m[4]), [g.strip('"') for g in m[5].split(',')]))
    return out
def count(sel):
    t = r.cmd(f'execute if entity @e[{sel}]'); m = re.search(r'(\d+)', t); return int(m.group(1)) if m and 'passed' in t else 0
fails = []
def check(ok, what):
    print(('  ok   ' if ok else '  FAIL ') + what)
    if not ok: fails.append(what)
def load(it, on=True):
    x0, y0, z0, x1, y1, z1 = it['box']; mid = (x0 + x1) // 2
    for a, b, c, d in ((x0, z0, mid, z1), (mid + 1, z0, x1, z1)): r.cmd(f"forceload {'add' if on else 'remove'} {a} {b} {c} {d}")
def survey(it, label):
    ns = npcs(it['id']); bad = 0
    for (x, y, z, yaw, tags) in ns:
        c = count(f'type=minecraft:villager,tag=bw.npc,x={x},y={y},z={z},distance=..0.7')
        kind = [g for g in tags if g.startswith('bw.npc.')][0]
        c2 = count(f'type=minecraft:villager,tag={kind},x={x},y={y},z={z},distance=..0.7' + ''.join(f',tag={g}' for g in tags if g.startswith('bw.t.')))
        bx, by, bz = math.floor(x), math.floor(y), math.floor(z)
        air = 'passed' in r.cmd(f'execute if block {bx} {by} {bz} #minecraft:air') and 'passed' in r.cmd(f'execute if block {bx} {by + 1} {bz} #minecraft:air')
        floor = 'failed' in r.cmd(f'execute if block {bx} {by - 1} {bz} #minecraft:air')
        if not (c == 1 and c2 == 1 and air and floor): bad += 1; print('      ', (x, y, z), kind, 'count', c, c2, 'air', air, 'floor', floor)
    x0, y0, z0, x1, y1, z1 = it['box']
    total = count(f'type=minecraft:villager,tag=bw.npc,x={x0},y={y0},z={z0},dx={x1 - x0},dy={y1 - y0},dz={z1 - z0}')
    check(bad == 0 and total == len(ns), f"{label} {it['id']}: {len(ns)} keepers wanted, {total} in the area, {bad} wrong spots")
    return ns
for it in info:
    load(it)
    t0 = time.time()
    while time.time() - t0 < 30:
        x0, y0, z0, x1, y1, z1 = it['box']
        if all('passed' in r.cmd(f'execute if loaded {x} 64 {z}') for x, z in ((x0, z0), (x1, z1), (x0, z1), (x1, z0), ((x0 + x1) // 2, (z0 + z1) // 2))): break
        time.sleep(0.5)
    ns = survey(it, 'installed')
    if it['id'] == 'tea':
        x, y, z = ns[0][:3]
        print('   kill one:', r.cmd(f'kill @e[type=minecraft:villager,tag=bw.npc,x={x},y={y},z={z},distance=..0.7]')[:60])
        time.sleep(1.5); gone = count(f'type=minecraft:villager,tag=bw.npc,x={x},y={y},z={z},distance=..0.7') == 0
        time.sleep(7.0)
        back = count(f'type=minecraft:villager,tag=bw.npc,x={x},y={y},z={z},distance=..0.7')
        check(gone and back == 1, f'a killed keeper is replaced within a few seconds (gone {gone}, back {back})')
        print('   ', r.cmd(f'data get entity @e[type=minecraft:villager,tag=bw.npc,x={x},y={y},z={z},distance=..0.7,limit=1] Tags')[:140])
        time.sleep(11.0); survey(it, 'two rounds later')
    load(it, False)
print('FAILS', fails)

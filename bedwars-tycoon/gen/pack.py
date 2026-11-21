"""Build every map and the lobby, then write the 'bedwars_maps' datapack (structures + install/teleport functions)."""
import sys, os, math, json, shutil, zipfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import themes, bwmap, lobby, check, render

ROOT = os.environ.get('BW_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = ROOT + '/out'
PACK = OUT + '/bedwars_maps'
Y0 = 64                                    # height of the bases' floor in the world
LOBBY = (0, Y0, 0)
def map_center(i): return (600 + 400 * i, Y0, 0)

def fn(path, lines):
    p = f'{PACK}/data/bw/function/{path}.mcfunction'
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

def tellraw(*parts):
    return 'tellraw @a ' + json.dumps([{'text': t, 'color': c} for t, c in parts], ensure_ascii=False)

def main(preview=True):
    t0 = time.time()
    if os.path.isdir(PACK): shutil.rmtree(PACK)
    os.makedirs(PACK + '/data/bw/structure'); os.makedirs(OUT + '/preview', exist_ok=True)
    json.dump({'pack': {'description': '배드워즈 맵 10개 + 로비', 'min_format': [121, 0], 'max_format': [121, 0]}},
              open(PACK + '/pack.mcmeta', 'w', encoding='utf-8'), ensure_ascii=False)
    items = []                     # (id, name, canvas, world centre)
    problems = 0
    for i, th in enumerate(themes.THEMES):
        cv = bwmap.build_map(th, th['R'], seed=100 + i)
        problems += len(check.check(cv, th['id'])) + len(check.markers(cv, th['id'])) + getattr(cv, 'overlap', 0)
        (x0, y0, z0), (x1, y1, z1) = cv.bounds()
        th['size'] = int(max(x1 - x0, z1 - z0) + 1)
        items.append((th['id'], th['name'], cv, map_center(i), th))
        if preview:
            bl = {p: (s.split('[')[0], 0) for p, s in cv.b.items()}
            render.render(bl, f"{OUT}/preview/{th['id']}_top.png", f"{OUT}/preview/{th['id']}_iso.png", 2)
    lcv, pads = lobby.build_lobby(themes.THEMES)
    problems += len(check.check(lcv, 'lobby'))
    if preview:
        bl = {p: (s.split('[')[0], 0) for p, s in lcv.b.items()}
        render.render(bl, f"{OUT}/preview/lobby_top.png", f"{OUT}/preview/lobby_iso.png", 2)
    items.insert(0, ('lobby', '로비', lcv, LOBBY, None))

    info = []
    for k, (iid, name, cv, (cx, cy, cz), th) in enumerate(items):
        org, size, n, npal = cv.save_structure(f'{PACK}/data/bw/structure/{iid}.nbt')
        px, py, pz = cx + int(org[0]), cy + int(org[1]), cz + int(org[2])
        ax, az = px + int(size[0]) - 1, pz + int(size[2]) - 1
        rec = dict(id=iid, name=name, place=[px, py, pz], size=[int(v) for v in size], blocks=n, center=[cx, cy, cz])
        if th is not None:
            sp = [p for p, t in cv.ents if 'bw.t.red' in [str(v) for v in t['Tags']] and 'bw.spawn' in [str(v) for v in t['Tags']]][0]
            wx, wy, wz = cx + sp[0], cy + sp[1], cz + sp[2]
            yaw = math.degrees(math.atan2(-(cx - wx), (cz - wz)))
            rec['tp'] = [round(wx, 1), round(wy, 1), round(wz, 1), round(yaw, 1)]
        info.append(rec)
        # install steps: forceload, wait until loaded, clear old entities, place, release
        nxt = items[k + 1][0] if k + 1 < len(items) else None
        midx, midz = (px + ax) // 2, (pz + az) // 2
        # forceload takes at most 256 chunks per command: split the area in two
        halves = [(px, pz, midx, az), (midx + 1, pz, ax, az)]
        fl_add = [f'forceload add {a} {b} {c} {d}' for a, b, c, d in halves]
        fl_rem = [f'forceload remove {a} {b} {c} {d}' for a, b, c, d in halves]
        for a, b, c, d in halves: assert ((c >> 4) - (a >> 4) + 1) * ((d >> 4) - (b >> 4) + 1) <= 256
        fn(f'install/{iid}/load', [*fl_add, f'schedule function bw:install/{iid}/try 40t'])
        fn(f'install/{iid}/try', [
            *fl_add,
            *[f'execute unless loaded {x} {cy} {z} run return run schedule function bw:install/{iid}/try 20t'
              for x, z in ((px, pz), (ax, pz), (px, az), (ax, az), (midx, midz))],
            f'kill @e[type=!player,tag=bw,x={px},y={py - 2},z={pz},dx={size[0]},dy={size[1] + 4},dz={size[2]}]',
            f'place template bw:{iid} {px} {py} {pz}',
            *fl_rem,
            f'scoreboard players set #installed bw {k + 1}',
            *(['execute if score #first bw matches 1 as @a run function bw:go/lobby', 'effect clear @a minecraft:slow_falling'] if iid == 'lobby' else []),
            tellraw(('[배드워즈] ', 'gold'), (f'{name} 설치 완료 ({k + 1}/{len(items)})', 'gray')),
            f'schedule function bw:install/{nxt}/load 10t' if nxt else 'function bw:install/done'])
    lob = [p for p, t in lcv.ents if 'bw.lobby.spawn' in [str(v) for v in t['Tags']]][0]
    LS = (LOBBY[0] + lob[0], LOBBY[1] + lob[1], LOBBY[2] + lob[2])
    fn('install/start', ['scoreboard players set #installed bw 0', tellraw(('[배드워즈] ', 'gold'), ('맵 10개와 로비를 설치할게. 1분쯤 걸려.', 'yellow')), f'function bw:install/{items[0][0]}/load'])
    fn('install/done', ['scoreboard players set #first bw 0', f'setworldspawn {math.floor(LS[0])} {math.floor(LS[1])} {math.floor(LS[2])}',
                        tellraw(('[배드워즈] ', 'gold'), ('설치 끝! ', 'green'), ('/function bw:lobby', 'aqua'), (' 로 로비에 갈 수 있어.', 'gray'))])
    # teleports
    fn('lobby', ['execute as @s[type=player] run function bw:go/lobby'])
    fn('go/lobby', [f'tp @s {LS[0]} {LS[1]} {LS[2]} 180 0', 'scoreboard players set @s lobby 0',
                    'title @s actionbar ' + json.dumps({'text': '로비', 'color': 'gold'}, ensure_ascii=False)])
    tick = ['scoreboard players enable @a lobby', 'execute as @a[scores={lobby=1..}] run function bw:go/lobby',
            # until the lobby exists (first start of a void world) nobody falls
            'execute unless score #installed bw matches 1.. run effect give @a minecraft:slow_falling 2 0 true']
    for rec, pad in zip(info[1:], pads):
        x, y, z, yaw = rec['tp']
        fn(f"go/{rec['id']}", [f'tp @s {x} {y} {z} {yaw} 10',
                               'title @s title ' + json.dumps({'text': rec['name'], 'color': 'gold', 'bold': True}, ensure_ascii=False),
                               'title @s subtitle ' + json.dumps({'text': f"{rec['size'][0]}x{rec['size'][2]} · 8팀 · 로비로: /trigger lobby", 'color': 'gray'}, ensure_ascii=False)])
        xs = [c[0] for c in pad['cells']]; zs = [c[1] for c in pad['cells']]
        bx, bz = LOBBY[0] + min(xs), LOBBY[2] + min(zs)
        dx, dz = max(xs) - min(xs) + 1, max(zs) - min(zs) + 1
        tick.append(f"execute as @a[x={bx},y={LOBBY[1] + 1},z={bz},dx={dx - 1},dy=1,dz={dz - 1},gamemode=!spectator] run function bw:go/{rec['id']}")
    fn('tick', tick)
    # first load in a world: install by itself (a later /reload does not reinstall; /function bw:install/start does)
    fn('load', ['scoreboard objectives add lobby trigger', 'scoreboard objectives add bw dummy',
                'execute unless score #installed bw matches 0.. run scoreboard players set #first bw 1',
                'execute unless score #installed bw matches 0.. run schedule function bw:install/start 1t'])
    os.makedirs(f'{PACK}/data/minecraft/tags/function', exist_ok=True)
    json.dump({'values': ['bw:load']}, open(f'{PACK}/data/minecraft/tags/function/load.json', 'w'))
    json.dump({'values': ['bw:tick']}, open(f'{PACK}/data/minecraft/tags/function/tick.json', 'w'))
    json.dump(info, open(OUT + '/maps.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # zip
    zp = OUT + '/bedwars_maps.zip'
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for dp, _, fs in os.walk(PACK):
            for f in sorted(fs):
                full = os.path.join(dp, f); z.write(full, os.path.relpath(full, PACK).replace(os.sep, '/'))
    for r in info:
        print(f"{r['id']:9s} {r['name']:8s} size {r['size'][0]}x{r['size'][2]} h{r['size'][1]} blocks {r['blocks']:6d} at {r['place']}  tp {r.get('tp')}")
    print('problems', problems, 'zip', os.path.getsize(zp) // 1024, 'KB', f'{time.time() - t0:.0f}s')
    return info

if __name__ == '__main__':
    main('nopreview' not in sys.argv)

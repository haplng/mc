"""Write the 'bedwars_maps' datapack, version 3: ten new maps + the lobby, installing themselves on first load.
A world that still has the version 2 maps is upgraded in place: every old volume is emptied right before the new build is placed."""
import sys, os, math, json, shutil, zipfile, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build

ROOT = build.ROOT
OUT = build.OUT
PACK = OUT + '/bedwars_maps'
VER = 3
Y0 = 64
LOBBY = (0, Y0, 0)
def map_center(i): return (600 + 400 * i, Y0, 0)

def fn(path, lines):
    p = f'{PACK}/data/bw/function/{path}.mcfunction'
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write('\n'.join(l for l in lines if l) + '\n')

def tellraw(*parts):
    return 'tellraw @a ' + json.dumps([{'text': t, 'color': c} for t, c in parts], ensure_ascii=False)

def slices(box, limit=32768):
    """cut a box into fills of at most `limit` blocks"""
    x0, y0, z0, x1, y1, z1 = box; h = y1 - y0 + 1
    sx = 16; sz = max(1, min(32, limit // (sx * h)))
    out = []
    for x in range(x0, x1 + 1, sx):
        for z in range(z0, z1 + 1, sz):
            out.append((x, y0, z, min(x + sx - 1, x1), y1, min(z + sz - 1, z1)))
    return out

def main(previews=True):
    t0 = time.time()
    if os.path.isdir(PACK): shutil.rmtree(PACK)
    os.makedirs(PACK + '/data/bw/structure')
    json.dump({'pack': {'description': '배드워즈 맵 10개 + 로비 (v3)', 'min_format': [121, 0], 'max_format': [121, 0]}},
              open(PACK + '/pack.mcmeta', 'w', encoding='utf-8'), ensure_ascii=False)
    recs, problems = build.build_maps(PACK + '/data/bw/structure', previews)
    json.dump(recs, open(OUT + '/maps_in.json', 'w', encoding='utf-8'), ensure_ascii=False)
    r = subprocess.run([sys.executable, ROOT + '/gen/lobby3.py', OUT + '/maps_in.json', PACK + '/data/bw/structure/lobby.nbt', OUT + '/lobby.json', OUT + '/canvas/lobby.pkl'],
                       capture_output=True, text=True)
    print(r.stdout.strip(), r.stderr.strip()[-600:])
    assert r.returncode == 0
    lob = json.load(open(OUT + '/lobby.json')); problems += lob['bad']
    items = [dict(id='lobby', name='로비', origin=lob['origin'], size=lob['size'], center=list(LOBBY), blocks=lob['blocks'])]
    for i, rec in enumerate(recs): rec['center'] = list(map_center(i)); items.append(rec)
    old = json.load(open(os.path.dirname(os.path.abspath(__file__)) + '/v2_places.json'))     # where version 2 put its lobby and maps
    assert len(old) == len(items)
    info = []
    for k, it in enumerate(items):
        cx, cy, cz = it['center']; ox, oy, oz = it['origin']; sx, sy, sz = it['size']
        px, py, pz = cx + ox, cy + oy, cz + oz; ax, ay, az = px + sx - 1, py + sy - 1, pz + sz - 1
        o = old[k]; qx, qy, qz = o['place']; q = o['size']
        box = (min(px, qx) - 1, min(py, qy) - 1, min(pz, qz) - 1, max(ax, qx + q[0] - 1) + 1, max(ay, qy + q[1] - 1) + 1, max(az, qz + q[2] - 1) + 1)
        it.update(place=[px, py, pz], box=list(box)); iid = it['id']; name = it['name']
        bx0, by0, bz0, bx1, by1, bz1 = box
        midx = (bx0 + bx1) // 2
        hv = [(bx0, bz0, midx, bz1), (midx + 1, bz0, bx1, bz1)]
        for a, b, c, d in hv: assert ((c >> 4) - (a >> 4) + 1) * ((d >> 4) - (b >> 4) + 1) <= 256
        fl_add = [f'forceload add {a} {b} {c} {d}' for a, b, c, d in hv]; fl_rem = [f'forceload remove {a} {b} {c} {d}' for a, b, c, d in hv]
        sel = f'x={bx0},y={by0},z={bz0},dx={bx1 - bx0},dy={by1 - by0},dz={bz1 - bz0}'
        nxt = items[k + 1]['id'] if k + 1 < len(items) else None
        fn(f'step/{iid}/load', [*fl_add, f'schedule function bw:step/{iid}/try 40t'])
        fn(f'step/{iid}/try', [
            *fl_add,
            *[f'execute unless loaded {x} {cy} {z} run return run schedule function bw:step/{iid}/try 20t'
              for x, z in ((bx0, bz0), (bx1, bz0), (bx0, bz1), (bx1, bz1), ((bx0 + bx1) // 2, (bz0 + bz1) // 2))],
            f'kill @e[type=!player,tag=bw,{sel}]',
            f'execute if score #wipe bw matches 1 run function bw:step/{iid}/wipe',
            f'place template bw:{iid} {px} {py} {pz}',
            *(['execute if score #first bw matches 1 as @a run function bw:go/lobby', 'effect clear @a minecraft:slow_falling'] if iid == 'lobby' else []),
            f'schedule function bw:step/{iid}/finish 10t'])
        fn(f'step/{iid}/wipe', [f'kill @e[type=item,{sel}]'] + [f'fill {a} {b} {c} {d} {e} {f} minecraft:air strict' for a, b, c, d, e, f in slices(box)])
        fn(f'step/{iid}/finish', [
            f'kill @e[type=item,{sel}]', f'kill @e[type=falling_block,{sel}]', *fl_rem,
            f'scoreboard players set #installed bw {k + 1}',
            tellraw(('[배드워즈] ', 'gold'), (f'{name} 설치 완료 ({k + 1}/{len(items)})', 'gray')),
            f'schedule function bw:step/{nxt}/load 10t' if nxt else 'function bw:install/done'])
        rec = dict(id=iid, name=name, place=[px, py, pz], size=[sx, sy, sz], blocks=it['blocks'], center=[cx, cy, cz], box=list(box))
        if 'red_spawn' in it:
            wx, wy, wz = cx + it['red_spawn'][0], cy + it['red_spawn'][1], cz + it['red_spawn'][2]
            yaw = math.degrees(math.atan2(-(cx - wx), (cz - wz)))
            rec['tp'] = [round(wx, 1), round(wy, 1), round(wz, 1), round(yaw, 1)]; rec['gaps'] = it['gaps']
        info.append(rec)
    LS = (LOBBY[0] + lob['spawn'][0], LOBBY[1] + lob['spawn'][1], LOBBY[2] + lob['spawn'][2])
    n = len(items)
    fn('install/start', ['scoreboard players set #installed bw 0', f'scoreboard players set #ver bw {VER}',
                         tellraw(('[배드워즈] ', 'gold'), ('로비와 맵 10개를 설치할게. 1~2분쯤 걸려.', 'yellow')), 'function bw:step/lobby/load'])
    fn('upgrade/start', [f'scoreboard players set #ver bw {VER}', 'scoreboard players set #wipe bw 1', 'scoreboard players set #first bw 1',
                         'scoreboard players set #installed bw 1', 'execute as @a run function bw:go/lobby',
                         tellraw(('[배드워즈] ', 'gold'), ('예전 맵을 지우고 새 맵 10개로 바꾸는 중이야. 2~3분쯤 걸려, 끝날 때까지 로비에 있어.', 'yellow')),
                         'function bw:step/lobby/load'])
    fn('reinstall', ['function bw:upgrade/start'])
    fn('install/done', ['scoreboard players set #first bw 0', 'scoreboard players set #wipe bw 0',
                        f'setworldspawn {math.floor(LS[0])} {math.floor(LS[1])} {math.floor(LS[2])}',
                        tellraw(('[배드워즈] ', 'gold'), ('설치 끝! 로비의 문으로 들어가면 맵으로 가. ', 'green'), ('/trigger lobby', 'aqua'), (' 로 로비에 돌아올 수 있어.', 'gray'))])
    fn('lobby', ['execute as @s[type=player] run function bw:go/lobby'])
    fn('go/lobby', [f'tp @s {LS[0]} {LS[1]} {LS[2]} 180 0', 'scoreboard players set @s lobby 0',
                    'title @s actionbar ' + json.dumps({'text': '로비', 'color': 'gold'}, ensure_ascii=False)])
    tick = ['scoreboard players enable @a lobby', 'execute as @a[scores={lobby=1..}] run function bw:go/lobby',
            'execute unless score #installed bw matches 1.. run effect give @a minecraft:slow_falling 2 0 true',
            # while old maps are being replaced nobody may stand on them: everyone waits in the lobby
            'execute if score #wipe bw matches 1 as @a unless entity @s[x=-110,y=-64,z=-110,dx=220,dy=400,dz=230] run function bw:go/lobby']
    for rec, pad in zip(info[1:], lob['pads']):
        x, y, z, yaw = rec['tp']
        fn(f"go/{rec['id']}", [f'tp @s {x} {y} {z} {yaw} 10',
                               'title @s title ' + json.dumps({'text': rec['name'], 'color': 'gold', 'bold': True}, ensure_ascii=False),
                               'title @s subtitle ' + json.dumps({'text': f"{rec['size'][0]}x{rec['size'][2]} · 8팀 · 로비로: /trigger lobby", 'color': 'gray'}, ensure_ascii=False)])
        xs = [c[0] for c in pad['cells']]; zs = [c[1] for c in pad['cells']]
        bx, bz = LOBBY[0] + min(xs), LOBBY[2] + min(zs)
        dx, dz = max(xs) - min(xs) + 1, max(zs) - min(zs) + 1
        tick.append(f"execute if score #installed bw matches {n}.. as @a[x={bx},y={LOBBY[1] + 1},z={bz},dx={dx - 1},dy=1,dz={dz - 1},gamemode=!spectator] run function bw:go/{rec['id']}")
    fn('tick', tick)
    fn('load', ['scoreboard objectives add lobby trigger', 'scoreboard objectives add bw dummy',
                # a world with the old maps (they never set #ver): swap them for the new ones
                f'execute if score #installed bw matches 0.. unless score #ver bw matches {VER}.. run schedule function bw:upgrade/start 20t',
                # a fresh world: install
                'execute unless score #installed bw matches 0.. run scoreboard players set #first bw 1',
                'execute unless score #installed bw matches 0.. run schedule function bw:install/start 1t'])
    os.makedirs(f'{PACK}/data/minecraft/tags/function', exist_ok=True)
    json.dump({'values': ['bw:load']}, open(f'{PACK}/data/minecraft/tags/function/load.json', 'w'))
    json.dump({'values': ['bw:tick']}, open(f'{PACK}/data/minecraft/tags/function/tick.json', 'w'))
    json.dump(info, open(OUT + '/maps.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    zp = OUT + '/bedwars_maps.zip'
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for dp, _, fs in os.walk(PACK):
            for f in sorted(fs):
                full = os.path.join(dp, f); z.write(full, os.path.relpath(full, PACK).replace(os.sep, '/'))
    for r in info:
        print(f"{r['id']:9s} {r['name']:5s} size {r['size'][0]}x{r['size'][2]} h{r['size'][1]} blocks {r['blocks']:6d} at {r['place']}  tp {r.get('tp')}")
    print('problems', problems, 'zip', os.path.getsize(zp) // 1024, 'KB', f'{time.time() - t0:.0f}s')
    return info

if __name__ == '__main__':
    main('nopreview' not in sys.argv)

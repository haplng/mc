"""Write the 'bedwars_maps' datapack (v9): the lobby, five maps, and the whole game that is played on them.
The pack installs itself on first load; a world that still has an older version is upgraded in place."""
import sys, os, math, json, shutil, zipfile, time, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build, lobby, check, mapdata, nav, game, gui, ai, hacks, items, extras
from util import Pack, snbt, t, tell

ROOT = build.ROOT
OUT = build.OUT
PACK = OUT + '/bedwars_maps'
VER = 8                                       # version of what stands in the world (lobby and maps): a change here makes worlds install anew
REL = 10                                      # version of the pack
Y0 = 64
LOBBY = (0, Y0, 0)
MARGIN = 12                                   # how far beyond a map a round may build
def map_center(i): return (600 + 400 * i, Y0, 0)

P = Pack(PACK)
def fn(path, lines): P.fn(path, lines)

def tellraw(*parts):
    return 'tellraw @a ' + json.dumps([{'text': t_, 'color': c} for t_, c in parts], ensure_ascii=False)

def slices(box, limit=32768):
    """cut a box into fills of at most `limit` blocks"""
    x0, y0, z0, x1, y1, z1 = box; h = y1 - y0 + 1
    sx = 16; sz = max(1, min(32, limit // (sx * h)))
    out = []
    for x in range(x0, x1 + 1, sx):
        for z in range(z0, z1 + 1, sz):
            out.append((x, y0, z, min(x + sx - 1, x1), y1, min(z + sz - 1, z1)))
    return out

NPC = {'shop': ('아이템 상점', 'minecraft:weaponsmith', 'aqua', 'plains'), 'upgrade': ('팀 업그레이드', 'minecraft:librarian', 'aqua', 'plains'),
       'unlock': ('업그레이드', 'minecraft:cleric', 'gold', 'plains'), 'black': ('???', 'minecraft:nitwit', 'dark_purple', 'swamp'),
       'hint': ('수상한 떠돌이', 'minecraft:nitwit', 'yellow', 'desert')}
def npc_cmd(n, cx, cy, cz, extra_tags=()):
    """one keeper: a villager that never moves, cannot be hurt and keeps its name above its head.
    It has no trades, so a right-click opens nothing of its own: the click is caught by an advancement."""
    name, prof, col, typ = NPC[n['kind']]
    x, y, z = n['pos']
    tags = ['bw', 'bw.npc', 'bw.npc.' + n['kind']] + (['bw.t.' + n['team']] if n.get('team') else []) + list(extra_tags)
    nbt = ('{NoAI:1b,Invulnerable:1b,Silent:1b,PersistenceRequired:1b,CanPickUpLoot:0b,CustomNameVisible:1b,'
           f'CustomName:{{text:"{name}",color:"{col}",bold:1b}},'
           f'VillagerData:{{type:"minecraft:{typ}",profession:"{prof}",level:5}},Offers:{{Recipes:[]}},'
           f'Rotation:[{n["yaw"]}f,0f],Tags:[{",".join(chr(34) + g + chr(34) for g in tags)}]}}')
    return f'summon minecraft:villager {cx + x} {cy + y} {cz + z} {nbt}'

def halves(x0, z0, x1, z1):
    midx = (x0 + x1) // 2
    hv = [(x0, z0, midx, z1), (midx + 1, z0, x1, z1)]
    for a, b, c, d in hv: assert ((c >> 4) - (a >> 4) + 1) * ((d >> 4) - (b >> 4) + 1) <= 256
    return hv

def main(previews=True):
    t0 = time.time()
    if os.path.isdir(PACK): shutil.rmtree(PACK)
    os.makedirs(PACK + '/data/bw/structure')
    json.dump({'pack': {'description': f'배드워즈 타이쿤 (v{REL}): 맵 5개 + 로비 + 게임', 'min_format': [121, 0], 'max_format': [121, 0]}},
              open(PACK + '/pack.mcmeta', 'w', encoding='utf-8'), ensure_ascii=False)
    recs, problems = build.build_maps(PACK + '/data/bw/structure', previews)
    lcv, pads, lspawn = lobby.build(recs)
    problems += len(check.states(lcv, 'lobby')); lph = check.physics(lcv, 'lobby')
    lorg, lsize, ln, lpal = lcv.save_structure(PACK + '/data/bw/structure/lobby.nbt')
    pickle.dump(dict(b=lcv.b), open(OUT + '/canvas/lobby.pkl', 'wb'))
    lob = dict(origin=[int(v) for v in lorg], size=[int(v) for v in lsize], blocks=ln, pads=pads, spawn=list(lspawn))
    json.dump(lob, open(OUT + '/lobby.json', 'w'))
    print(f'lobby     {lsize[0]}x{lsize[2]} h{lsize[1]} blocks {ln} physics fixed {sum(lph.values())}')
    if previews:
        import preview
        preview.iso2(lcv, 3, 0, 2.2).save(OUT + '/preview/lobby_iso.png'); preview.front(lcv, 5, zmin=-60, zmax=40).save(OUT + '/preview/lobby_front.png')
    ux, uy, uz, uyaw = lobby.UNLOCK_NPC; dx, dy, dz, dyaw = lobby.DEALER
    items_ = [dict(id='lobby', name='로비', origin=lob['origin'], size=lob['size'], center=list(LOBBY), blocks=lob['blocks'],
                   npcs=[dict(kind='unlock', team=None, pos=[ux + 0.5, uy, uz + 0.5], yaw=uyaw), dict(kind='black', team=None, pos=[dx + 0.5, dy, dz + 0.5], yaw=dyaw)])]
    for i, rec in enumerate(recs): rec['center'] = list(map_center(i)); items_.append(rec)
    prev = json.load(open(os.path.dirname(os.path.abspath(__file__)) + '/prev_boxes.json'))    # the boxes all earlier versions used: lobby + ten map slots
    ghosts = [dict(id=f'slot{n + 1}', center=g['center'], box=g['box']) for n, g in enumerate(prev) if n >= len(items_)]   # slots that only have to be emptied
    first_map = items_[1]['id']
    info = []
    for k, it in enumerate(items_):
        cx, cy, cz = it['center']; ox, oy, oz = it['origin']; sx, sy, sz = it['size']
        px, py, pz = cx + ox, cy + oy, cz + oz; ax, ay, az = px + sx - 1, py + sy - 1, pz + sz - 1
        assert prev[k]['center'] == [cx, cy, cz]
        q = prev[k]['box']
        box = (min(px - 1, q[0]), min(py - 1, q[1]), min(pz - 1, q[2]), max(ax + 1, q[3]), max(ay + 1, q[4]), max(az + 1, q[5]))
        it.update(place=[px, py, pz], box=list(box)); iid = it['id']; name = it['name']
        bx0, by0, bz0, bx1, by1, bz1 = box
        hv = halves(bx0, bz0, bx1, bz1)
        fl_add = [f'forceload add {a} {b} {c} {d}' for a, b, c, d in hv]; fl_rem = [f'forceload remove {a} {b} {c} {d}' for a, b, c, d in hv]
        sel = f'x={bx0},y={by0},z={bz0},dx={bx1 - bx0},dy={by1 - by0},dz={bz1 - bz0}'
        nxt = items_[k + 1]['id'] if k + 1 < len(items_) else None
        fn(f'step/{iid}/load', [*fl_add, f'schedule function bw:step/{iid}/try 40t'])
        fn(f'step/{iid}/try', [
            *fl_add,
            *[f'execute unless loaded {x} {cy} {z} run return run schedule function bw:step/{iid}/try 20t'
              for x, z in ((bx0, bz0), (bx1, bz0), (bx0, bz1), (bx1, bz1), ((bx0 + bx1) // 2, (bz0 + bz1) // 2))],
            f'kill @e[type=!player,tag=bw,{sel}]',
            f'execute if score #wipe bw matches 1 run function bw:step/{iid}/wipe',
            f'place template bw:{iid} {px} {py} {pz}',
            *[npc_cmd(n, cx, cy, cz) for n in it.get('npcs', [])],
            f'execute as @e[type=minecraft:marker,tag=bw.gui,{sel}] at @s run function bw:gui/init',
            *(['execute if score #first bw matches 1 as @a run function bw:go/lobby', 'effect clear @a minecraft:slow_falling'] if iid == 'lobby' else []),
            f'schedule function bw:step/{iid}/finish 10t'])
        fn(f'step/{iid}/wipe', [f'kill @e[type=item,{sel}]'] + [f'fill {a} {b} {c} {d} {e} {f} minecraft:air strict' for a, b, c, d, e, f in slices(box)])
        fn(f'step/{iid}/finish', [
            f'kill @e[type=item,{sel}]', f'kill @e[type=falling_block,{sel}]', *([] if iid == 'lobby' else fl_rem),
            f'scoreboard players set #installed bw {k + 1}',
            tellraw(('[배드워즈] ', 'gold'), (f'{name} 설치 완료 ({k + 1}/{len(items_)})', 'gray')),
            *(['forceload remove all', 'forceload add -1 -1 0 0',
               f'execute if score #wipe bw matches 1 run schedule function bw:step/{ghosts[0]["id"]}/load 10t',
               f'execute unless score #wipe bw matches 1 run schedule function bw:step/{first_map}/load 10t'] if iid == 'lobby' else
              [f'schedule function bw:step/{nxt}/load 10t' if nxt else 'function bw:install/done'])])
        rec = dict(id=iid, name=name, place=[px, py, pz], size=[sx, sy, sz], blocks=it['blocks'], center=[cx, cy, cz], box=list(box))
        if 'red_spawn' in it:
            wx, wy, wz = cx + it['red_spawn'][0], cy + it['red_spawn'][1], cz + it['red_spawn'][2]
            yaw = math.degrees(math.atan2(-(cx - wx), (cz - wz)))
            rec['tp'] = [round(wx, 1), round(wy, 1), round(wz, 1), round(yaw, 1)]; rec['gaps'] = it['gaps']
        info.append(rec)
    for g, gh in enumerate(ghosts):
        gid = gh['id']; bx0, by0, bz0, bx1, by1, bz1 = gh['box']; cy = gh['center'][1]
        hv = halves(bx0, bz0, bx1, bz1)
        fl_add = [f'forceload add {a} {b} {c} {d}' for a, b, c, d in hv]; fl_rem = [f'forceload remove {a} {b} {c} {d}' for a, b, c, d in hv]
        sel = f'x={bx0},y={by0},z={bz0},dx={bx1 - bx0},dy={by1 - by0},dz={bz1 - bz0}'
        nxt = ghosts[g + 1]['id'] if g + 1 < len(ghosts) else first_map
        fn(f'step/{gid}/load', [*fl_add, f'schedule function bw:step/{gid}/try 40t'])
        fn(f'step/{gid}/try', [
            *fl_add,
            *[f'execute unless loaded {x} {cy} {z} run return run schedule function bw:step/{gid}/try 20t'
              for x, z in ((bx0, bz0), (bx1, bz0), (bx0, bz1), (bx1, bz1), ((bx0 + bx1) // 2, (bz0 + bz1) // 2))],
            f'kill @e[type=!player,tag=bw,{sel}]', f'kill @e[type=item,{sel}]',
            *[f'fill {a} {b} {c} {d} {e} {f} minecraft:air strict' for a, b, c, d, e, f in slices(gh['box'])],
            f'schedule function bw:step/{gid}/finish 10t'])
        fn(f'step/{gid}/finish', [f'kill @e[type=item,{sel}]', f'kill @e[type=falling_block,{sel}]', *fl_rem,
                                  tellraw(('[배드워즈] ', 'gold'), (f'안 쓰는 예전 맵 자리 비움 ({g + 1}/{len(ghosts)})', 'gray')),
                                  f'schedule function bw:step/{nxt}/load 10t'])
        info.append(dict(id=gid, name='(비움)', box=list(gh['box']), center=gh['center'], empty=True))
    LS = (LOBBY[0] + lob['spawn'][0], LOBBY[1] + lob['spawn'][1], LOBBY[2] + lob['spawn'][2])
    n = len(items_)
    fn('install/start', ['scoreboard players set #installed bw 0', f'scoreboard players set #ver bw {VER}',
                         tellraw(('[배드워즈] ', 'gold'), ('로비와 맵 5개를 설치할게. 1분쯤 걸려.', 'yellow')), 'function bw:step/lobby/load'])
    fn('upgrade/start', ['forceload remove all', f'scoreboard players set #ver bw {VER}', 'scoreboard players set #wipe bw 1', 'scoreboard players set #first bw 1',
                         'scoreboard players set #installed bw 1', 'scoreboard players set #state bw 0', 'execute as @a run function bw:go/lobby',
                         tellraw(('[배드워즈] ', 'gold'), ('새 버전으로 로비와 맵을 다시 까는 중이야. 1~2분쯤 걸려, 끝날 때까지 로비에 있어.', 'yellow')),
                         'function bw:step/lobby/load'])
    # an older pack may have been interrupted in the middle of its own install: drop whatever it left scheduled
    old_ids = ['lobby', 'tea', 'chess', 'circus', 'train', 'stadium', 'library', 'turtle', 'windmill', 'solar', 'pirate',
               'library_old', 'turtle_old', 'windmill_old', 'solar_old', 'pirate_old']
    stale = sorted({f'bw:step/{i}/{w}' for i in old_ids + [it['id'] for it in items_] + [g['id'] for g in ghosts] for w in ('load', 'try', 'finish')}
                   | {'bw:install/start', 'bw:upgrade/start'})
    fn('upgrade/prepare', [f'schedule clear {f}' for f in stale] + ['schedule function bw:upgrade/start 20t'])
    fn('reinstall', ['function bw:upgrade/prepare'])
    fn('install/done', ['scoreboard players set #first bw 0', 'scoreboard players set #wipe bw 0',
                        f'setworldspawn {math.floor(LS[0])} {math.floor(LS[1])} {math.floor(LS[2])}',
                        tellraw(('[배드워즈] ', 'gold'), ('설치 끝! 로비의 성문으로 들어가면 그 맵에서 게임이 시작돼. ', 'green'), ('/trigger lobby', 'aqua'), (' 로 언제든 로비에 돌아올 수 있어.', 'gray'))])
    fn('lobby', ['execute as @s[type=player] run function bw:go/lobby'])
    lobby_tp = f'{LS[0]} {LS[1]} {LS[2]} 180 0'
    # /trigger lobby: in a round it gives up the round
    fn('go/lobby', ['scoreboard players set @s lobby 0',
                    'execute if score #state bw matches 1.. if entity @s[tag=bw.play] run return run function bw:game/giveup',
                    f'tp @s {lobby_tp}', 'title @s actionbar ' + json.dumps({'text': '로비', 'color': 'gold'}, ensure_ascii=False)])
    fn('game/giveup', [tell('@a', {'selector': '@s'}, t('이(가) 게임을 포기했어.', 'gray')), 'function bw:game/close'])

    # ------------------------------------------------------------------ the game
    maps = []; navs = {}; resets = {}
    blocks_json = json.load(open(ROOT + '/ref/263_blocks_data.json'))
    # an untouched copy of every map stands far to the south: it tells what a player built from what is map (extras.py)
    ZOFF, COPYGEN = extras.copy_offset(PACK + '/data/bw/structure', [rec['id'] for rec in recs])
    for rec in recs:
        mid = rec['id']; m = mapdata.load(mid, tuple(rec['center']), OUT); m['name'] = rec['name']
        nv = navs[mid] = nav.plan(mid, OUT)
        cx, cy, cz = rec['center']; px, py, pz = rec['place']; sx, sy, sz = rec['size']
        x0, z0, x1, z1 = px - MARGIN, pz - MARGIN, px + sx - 1 + MARGIN, pz + sz - 1 + MARGIN
        y0 = m['void_y'] - 2; y1 = m['top_y'] + 26
        hv = halves(x0, z0, x1, z1) + halves(x0, z0 + ZOFF, x1, z1 + ZOFF)
        sel = f'x={x0},y={y0 - 20},z={z0},dx={x1 - x0},dy={y1 - y0 + 60},dz={z1 - z0}'
        csel = f'x={x0},y={y0 - 20},z={z0 + ZOFF},dx={x1 - x0},dy={y1 - y0 + 60},dz={z1 - z0}'
        hint = nv.get('hint'); d0 = nv.get('dia0')
        place = [f'place template bw:{mid} {px} {py} {pz}', *[npc_cmd(n, cx, cy, cz) for n in rec.get('npcs', [])],
                 f'execute as @e[type=minecraft:marker,tag=bw.gui,{sel}] at @s run function bw:gui/init']
        if hint:
            yaw = round(math.degrees(math.atan2(-(d0[0] - hint[0]), d0[2] - hint[2])) / 90) * 90.0
            place.append(npc_cmd(dict(kind='hint', team=None, pos=[hint[0] + 0.5, hint[1], hint[2] + 0.5], yaw=yaw), cx, cy, cz, ['bw.round']))
        resets[mid] = dict(
            forceload=[f'forceload add {a} {b} {c} {d}' for a, b, c, d in hv], unload=[f'forceload remove {a} {b} {c} {d}' for a, b, c, d in hv],
            corners=[(x, cy, z + dz_) for dz_ in (0, ZOFF) for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1), ((x0 + x1) // 2, (z0 + z1) // 2))],
            copy=[f'place template bw:{mid} {px} {py} {pz + ZOFF}', f'kill @e[type=!minecraft:player,{csel}]'], copygen=COPYGEN,
            kill=[f'kill @e[type=!minecraft:player,tag=bw,{sel}]', f'kill @e[type=minecraft:item,{sel}]', f'kill @e[type=minecraft:arrow,{sel}]'],
            wipe=[f'fill {a} {b} {c} {d} {e} {f} minecraft:air replace #bw:reset' for a, b, c, d, e, f in slices((x0, y0, z0, x1, y1, z1))],
            place=place, border=sx + 2 * MARGIN, ymax=y1 - 2)
        maps.append(m)
    g = game.write(P, maps, dict(tp=lobby_tp, spawn=(math.floor(LS[0]), math.floor(LS[1]), math.floor(LS[2]))), resets, n)
    icons = {'tea': 'cake', 'chess': 'quartz_pillar', 'circus': 'red_banner', 'library': 'bookshelf', 'solar': 'sunflower'}
    G = gui.write(P, [dict(id=r_['id'], name=r_['name'], size=f"{r_['size'][0]}x{r_['size'][2]}", price=game.MAP_PRICE[r_['id']], bonus=game.MAP_BONUS[r_['id']], icon=icons[r_['id']]) for r_ in recs])
    a = ai.write(P, maps, navs)
    ai.block_tags(P, blocks_json, lambda name: nav.is_open('minecraft:' + name))
    extras.block_tags(P, blocks_json, lambda name: nav.is_open('minecraft:' + name), ai.SOFT)
    ex = extras.write(P, maps, resets, ZOFF)
    h = hacks.write(P, G, maps, navs)
    hacks.npcs(P, maps)
    gui.npc_hints(P, PACK)
    gg = G.finish()

    tick = ['scoreboard players enable @a lobby', 'execute as @a[scores={lobby=1..}] run function bw:go/lobby',
            'execute unless score #installed bw matches 1.. run effect give @a minecraft:slow_falling 2 0 true',
            # while old maps are being replaced nobody may stand on them: everyone waits in the lobby
            'execute if score #wipe bw matches 1 as @a unless entity @s[x=-110,y=-64,z=-110,dx=220,dy=400,dz=230] run function bw:go/lobby']
    for rec, pad in zip([r for r in info if 'tp' in r], lob['pads']):
        xs = [c[0] for c in pad['cells']]; zs = [c[1] for c in pad['cells']]
        bx, bz = LOBBY[0] + min(xs), LOBBY[2] + min(zs)
        ddx, ddz = max(xs) - min(xs) + 1, max(zs) - min(zs) + 1
        tick.append(f"execute if score #state bw matches 0 if score #installed bw matches {n}.. as @a[x={bx},y={LOBBY[1] + 1},z={bz},dx={ddx - 1},dy=1,dz={ddz - 1},gamemode=!spectator,limit=1] run function bw:game/pick/{rec['id']}")
    # the keepers heal themselves: every five seconds, each spot in a loaded chunk that has lost its keeper gets a new one
    ensure = []
    for it in items_:
        cx, cy, cz = it['center']
        for npc in it.get('npcs', []):
            nbt = npc_cmd(npc, cx, cy, cz).split(' ', 5)[5]
            ensure.append(f"execute positioned {cx + npc['pos'][0]} {cy + npc['pos'][1]} {cz + npc['pos'][2]} if loaded ~ ~ ~ "
                          f'unless entity @e[type=minecraft:villager,tag=bw.npc,distance=..0.7] run summon minecraft:villager ~ ~ ~ {nbt}')
    fn('npc/ensure', ['scoreboard players set #npc bw 0'] + ensure)
    tick += ['scoreboard players add #npc bw 1',
             f'execute if score #npc bw matches 100.. if score #installed bw matches {n}.. unless score #wipe bw matches 1 unless score #state bw matches 1..2 run function bw:npc/ensure',
             # two helpers live at the world's origin: an arrow that turns a direction into numbers, and a hand that reads what was clicked
             'execute if score #npc bw matches 50 run function bw:core/helpers']
    fn('core/helpers', ['forceload add -1 -1 0 0',
                        'execute if loaded 0 0 0 unless entity @e[type=minecraft:marker,tag=bw.vec] run summon minecraft:marker 0.0 0.0 0.0 {Tags:["bw.vec"]}',
                        'execute if loaded 0 0 0 unless entity @e[type=minecraft:armor_stand,tag=bw.tmp] run summon minecraft:armor_stand 0.5 -60 0.5 {Marker:1b,Invisible:1b,NoGravity:1b,Invulnerable:1b,Tags:["bw.tmp"]}'])
    fn('tick', tick + g['tick'] + a['tick'] + h['tick'] + gg['tick'])
    fn('load', ['scoreboard objectives add lobby trigger', 'scoreboard objectives add bw dummy', *g['load'], *gg['load'], *a['load'], *h['load'], *ex['load'],
                'forceload add -1 -1 0 0',
                # a world with an older version: swap it for this one
                f'execute if score #installed bw matches 0.. unless score #ver bw matches {VER}.. run function bw:upgrade/prepare',
                # a fresh world: install
                'execute unless score #installed bw matches 0.. run scoreboard players set #first bw 1',
                'execute unless score #installed bw matches 0.. run schedule function bw:install/start 1t'])
    os.makedirs(f'{PACK}/data/minecraft/tags/function', exist_ok=True)
    json.dump({'values': ['bw:load']}, open(f'{PACK}/data/minecraft/tags/function/load.json', 'w'))
    json.dump({'values': ['bw:tick']}, open(f'{PACK}/data/minecraft/tags/function/tick.json', 'w'))
    json.dump(info, open(OUT + '/maps.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    zp = OUT + '/bedwars_maps.zip'
    nfiles = 0
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for dp, _, fs in os.walk(PACK):
            for f in sorted(fs):
                full = os.path.join(dp, f); z.write(full, os.path.relpath(full, PACK).replace(os.sep, '/')); nfiles += 1
    for r in info:
        if not r.get('empty'): print(f"{r['id']:9s} {r['name']:5s} size {r['size'][0]}x{r['size'][2]} h{r['size'][1]} blocks {r['blocks']:6d} at {r['place']}")
    print('problems', problems, 'files', nfiles, 'functions', len(P.fns), 'zip', os.path.getsize(zp) // 1024, 'KB', f'{time.time() - t0:.0f}s')
    return info

if __name__ == '__main__':
    main('nopreview' not in sys.argv)

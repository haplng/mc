"""The bed wars lobby: a big floating island with a fountain plaza, a hub hall, ten map gates and showpiece islands."""
import math
from nbtlib import Compound, String, Byte, Float, List, Int
from canvas import Canvas
import parts as PT
from themes import ring, disc, pond, pillar, castle_tower

LOBBY_TH = dict(
    top=[('grass_block', 8), ('moss_block', 1)], sub=[('dirt', 3), ('coarse_dirt', 1)],
    under=[('stone', 3), ('andesite', 2), ('dirt', 1), ('tuff', 1)],
    strata=['terracotta', 'brown_terracotta', 'terracotta', 'light_gray_terracotta', 'stone', 'andesite', 'stone', 'tuff', 'brown_terracotta', 'stone'],
    tip=[('tuff', 2), ('stone', 1)], hang={'body': 'cave_vines_plant[berries=true]', 'end': 'cave_vines[age=0,berries=true]'},
    flora=[('short_grass', 6), ('poppy', 1), ('dandelion', 1), ('cornflower', 1), ('oxeye_daisy', 1), ('fern', 1), ('rose_bush|tall', 1), ('lilac|tall', 1)],
)

def sign(cv, x, y, z, lines, rotation=None, facing=None, wood='dark_oak'):
    """a waxed sign (standing with rotation 0-15, or on a wall with facing); lines: up to 4 (text, colour)"""
    msgs = []
    for i in range(4):
        t, c = lines[i] if i < len(lines) else ('', 'black')
        msgs.append(Compound({'text': String(t), 'color': String(c)}))
    side = lambda m: Compound({'messages': List[Compound](m), 'has_glowing_text': Byte(1), 'color': String('black')})
    blank = [Compound({'text': String('')}) for _ in range(4)]
    if facing: cv.set(x, y, z, f'{wood}_wall_sign[facing={facing}]')
    else: cv.set(x, y, z, f'{wood}_sign[rotation={rotation % 16}]')
    cv.nbt[(x, y, z)] = Compound({'id': String('minecraft:sign'), 'front_text': side(msgs), 'back_text': side(blank), 'is_waxed': Byte(1)})

FONT = {'B': ['110', '101', '110', '101', '110'], 'E': ['111', '100', '110', '100', '111'], 'D': ['110', '101', '101', '101', '110'],
        'W': ['10001', '10001', '10101', '10101', '01010'], 'A': ['010', '101', '111', '101', '101'], 'R': ['110', '101', '110', '101', '101'],
        'S': ['011', '100', '010', '001', '110'], ' ': ['00', '00', '00', '00', '00']}

def block_text(cv, x, y, z, text, colours):
    """big letters on the x-y plane, top row at y+4"""
    ci = 0
    for ch in text:
        g = FONT[ch]
        col = colours[ci % len(colours)] if ch != ' ' else None
        for r, row in enumerate(g):
            for c, bit in enumerate(row):
                if bit == '1': cv.set(x + c, y + 4 - r, z, f'{col}_concrete')
        x += len(g[0]) + (0 if ch == ' ' else 1)
        if ch != ' ': ci += 1
    return x

def gate(cv, x, z, ang, th, idx):
    """an arch for one map, facing the plaza; returns the pad cells"""
    P = th['house']; fx, fz = round(math.cos(ang)), round(math.sin(ang))
    # local axes: u along the arch (perpendicular to the radius)
    ux, uz = -math.sin(ang), math.cos(ang)
    cells = []
    for s in range(-3, 4):
        px, pz = round(x + ux * s), round(z + uz * s)
        if abs(s) == 3:
            for y in range(1, 7): cv.set(px, y, pz, P['frame'] if 'log' not in P['frame'] and 'pillar' not in P['frame'] else P['frame'])
        cv.set(px, 7, pz, P['roof_full'])
        cv.set(px, 8, pz, P['roof_full'] if abs(s) <= 1 else None)
        if abs(s) == 2: cv.set(px, 6, pz, P['roof_full'])
    for s in (-3, 3):
        px, pz = round(x + ux * s), round(z + uz * s)
        cv.set(px, 0, pz, 'polished_andesite'); cv.set(round(px + math.cos(ang)), 0, round(pz + math.sin(ang)), 'polished_andesite')
    # glowing pad inside the arch: the map's own ground
    for s in range(-2, 3):
        for r in (0, -1, 1):
            px, pz = round(x + ux * s + math.cos(ang) * r), round(z + uz * s + math.sin(ang) * r)
            cv.set(px, 0, pz, 'sea_lantern' if (s, r) == (0, 0) else cv.pick(th['plaza']))
            cells.append((px, pz))
            for y in range(1, 6):
                if abs(s) < 3: cv.set(px, y, pz, None)
    # coloured glass curtain hanging under the lintel
    for s in range(-2, 3):
        px, pz = round(x + ux * s), round(z + uz * s)
        cv.set(px, 6, pz, th.get('gate_glass', 'light_blue_stained_glass'))
    return cells

def giant_bed(cv, x, y, z):
    for dx in range(-3, 4):
        for dz in range(-6, 7):
            cv.set(x + dx, y, z + dz, 'oak_planks')
            for h in (1, 2): cv.set(x + dx, y + h, z + dz, 'white_wool' if dz < -2 else 'red_wool')
        for h in (3,):
            if -2 <= dz <= 6: pass
    for dx in (-3, 3):
        for dz in (-6, 6):
            for h in (-1, -2): cv.set(x + dx, y + h, z + dz, 'oak_log')
    for dx in range(-3, 4): cv.set(x + dx, y + 3, z - 6, 'oak_planks'); cv.set(x + dx, y + 4, z - 6, 'oak_planks')
    for dx in range(-2, 3): cv.set(x + dx, y + 3, z - 4, 'white_wool')

def giant_tnt(cv, x, y, z, s=6):
    for dx in range(s):
        for dy in range(s):
            for dz in range(s):
                edge = dx in (0, s - 1) or dz in (0, s - 1) or dy in (0, s - 1)
                if not edge: continue
                band = 2 <= dy <= s - 3
                b = 'white_concrete' if band else 'red_concrete'
                if dy == s - 1 and 0 < dx < s - 1 and 0 < dz < s - 1: b = 'light_gray_concrete'
                if band and (dx in (0, s - 1)) and (dz % 2 == 0): b = 'black_concrete' if dy == s // 2 else 'white_concrete'
                cv.set(x + dx, y + dy, z + dz, b)
    cv.set(x + s // 2, y + s, z + s // 2, 'oak_fence'); cv.set(x + s // 2, y + s + 1, z + s // 2, 'fire') if False else None

def giant_gem(cv, x, y, z, r, core, shell):
    for dy in range(-r, r + 1):
        rr = r - abs(dy)
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) + abs(dz) <= rr:
                    cv.set(x + dx, y + dy, z + dz, shell if abs(dx) + abs(dz) == rr or abs(dy) == r else core)

def giant_sword(cv, x, y, z):
    # a sword stuck in the ground, blade along y, flat in the x-y plane
    for i in range(14):
        cv.set(x, y + i, z, 'iron_block');
        if i < 12: cv.set(x + 1, y + i, z, 'light_gray_concrete') if i % 2 else cv.set(x - 1, y + i, z, 'light_gray_concrete')
    for dx in range(-3, 4): cv.set(x + dx, y + 14, z, 'gold_block')
    for i in range(15, 19): cv.set(x, y + i, z, 'stripped_spruce_log[axis=y]')
    cv.set(x, y + 19, z, 'gold_block')

def hall_inside(cv, hx0, hx1, hz0, hz1):
    """the lobby hall: a red runner, a dais with the eight team beds, shop booths, benches and chandeliers"""
    dyes = ['red', 'blue', 'lime', 'yellow', 'cyan', 'white', 'pink', 'gray']
    for x in range(hx0 + 1, hx1):
        for z in range(hz0 + 1, hz1):
            cv.set(x, 0, z, 'polished_andesite' if (x + z) % 2 else 'smooth_stone')
    for z in range(hz0 + 3, hz1):
        for x in (-1, 0, 1): cv.set(x, 1, z, 'red_carpet')
    # dais with the eight beds and the team banners above them
    for x in range(-9, 10):
        for z in (hz0 + 1, hz0 + 2): cv.set(x, 1, z, 'polished_diorite')
        cv.set(x, 1, hz0 + 3, 'polished_diorite_slab[type=bottom]') if abs(x) > 1 else None
    for k, dye in enumerate(dyes):
        x = -8 + k * 2 + (1 if k >= 4 else 0)
        cv.set(x, 2, hz0 + 2, f'{dye}_bed[facing=north,part=foot]'); cv.set(x, 2, hz0 + 1, f'{dye}_bed[facing=north,part=head]')
        cv.set(x, 6, hz0 + 1, f'{dye}_wall_banner[facing=south]')
    # shop booths along the side walls: a counter, a workstation behind it, a striped awning
    stations = ['cartography_table', 'smithing_table', 'fletching_table', 'loom', 'lectern[facing=east]', 'brewing_stand']
    k = 0
    for side, wx in ((-1, hx0), (1, hx1)):
        for zc in (hz0 + 5, hz1 - 5):
            cx = wx - side * 3
            for dz in (-1, 0, 1):
                cv.set(cx, 1, zc + dz, 'barrel[facing=up]' if dz == 0 else 'spruce_planks')
                cv.set(cx, 2, zc + dz, 'spruce_slab[type=bottom]' if dz else 'potted_fern')
                for ax in range(wx - side * 1, cx + side * 0 - side, -side):
                    cv.set(ax, 4, zc + dz, f'{dyes[k % 8]}_wool' if (ax + dz) % 2 == 0 else 'white_wool')
            cv.set(wx - side, 1, zc, stations[k % len(stations)])
            k += 1
    # benches round the middle, chandeliers overhead
    for x in (-6, -4, 4, 6):
        for z in (hz0 + 6, hz0 + 9):
            cv.set(x, 1, z, 'dark_oak_stairs[facing=%s,half=bottom]' % ('west' if x < 0 else 'east'))
    for x in (-8, 0, 8):
        z = (hz0 + hz1) // 2
        for y in (10, 9): cv.set(x, y, z, 'iron_chain[axis=y]')
        cv.set(x, 8, z, 'lantern[hanging=true]')
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)): cv.set(x + dx, 8, z + dz, 'iron_chain[axis=x]' if dx else 'iron_chain[axis=z]')
        for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2)): cv.set(x + dx, 8, z + dz, 'lantern[hanging=false]')
    for x, z in ((hx0 + 1, hz1 - 1), (hx1 - 1, hz1 - 1), (hx0 + 1, hz0 + 1), (hx1 - 1, hz0 + 1)):
        cv.set(x, 1, z, 'potted_azalea_bush')
    for x in (hx0 + 1, hx1 - 1):
        for z in range(hz0 + 2, hz1 - 1, 3):
            if cv.empty(x, 1, z): cv.set(x, 1, z, 'bookshelf'); cv.set(x, 2, z, 'bookshelf')

def build_lobby(map_themes, seed=7):
    cv = Canvas(seed)
    th = LOBBY_TH
    RX, RZ = 58, 54
    hm = PT.island(cv, 0, 0, 0, RX, RZ, 40, th, seed, flat=0.74, hill=2.0)
    PT.flatten(cv, hm, -30, -30, 30, 30, 0, th)
    # plaza
    for x in range(-14, 15):
        for z in range(-14, 15):
            d = math.hypot(x, z)
            if d < 13.5:
                band = int(d) % 4
                cv.set(x, 0, z, 'polished_andesite' if band == 0 else 'stone_bricks' if band in (1, 3) else 'polished_diorite')
            elif d < 14.5: cv.set(x, 0, z, 'chiseled_stone_bricks' if (x + z) % 3 == 0 else 'stone_bricks')
    # fountain
    for x in range(-5, 6):
        for z in range(-5, 6):
            d = math.hypot(x, z)
            if d < 4: cv.set(x, 0, z, 'water'); cv.set(x, -1, z, 'prismarine_bricks')
            elif d < 5: cv.set(x, 0, z, 'quartz_bricks'); cv.set(x, 1, z, 'quartz_slab[type=bottom]')
    for i in range(1, 5): cv.set(0, i, 0, 'quartz_pillar[axis=y]')
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)): cv.set(dx, 4, dz, 'quartz_stairs[facing=%s,half=top]' % {(1, 0): 'west', (-1, 0): 'east', (0, 1): 'north', (0, -1): 'south'}[(dx, dz)])
    cv.set(0, 5, 0, 'sea_lantern'); cv.set(0, 6, 0, 'red_bed[facing=south,part=foot]'); cv.set(0, 6, 1, 'red_bed[facing=south,part=head]')
    for k in range(8):
        a = k * math.pi / 4
        PT.lantern_post(cv, round(11 * math.cos(a)), 1, round(11 * math.sin(a)), 'dark_oak_fence', 'lantern', 3)
    # hub hall to the north
    hx0, hx1, hz0, hz1 = -16, 16, -46, -32
    PT.flatten(cv, hm, hx0 - 2, hz0 - 2, hx1 + 2, hz1 + 3, 0, th)
    for x in range(hx0, hx1 + 1):
        for z in range(hz0, hz1 + 1):
            cv.set(x, 0, z, 'polished_andesite')
            edge = x in (hx0, hx1) or z in (hz0, hz1)
            for y in range(1, 12):
                if edge:
                    s = 'bricks' if y < 11 else 'stone_bricks'
                    if (x - hx0) % 4 == 0 or (z - hz0) % 4 == 0 and x in (hx0, hx1): s = 'stripped_dark_oak_log[axis=y]' if y < 11 else s
                    if 3 <= y <= 5 and (x - hx0) % 4 == 2 and z in (hz0, hz1): s = 'cyan_stained_glass'
                    if 3 <= y <= 5 and (z - hz0) % 4 == 2 and x in (hx0, hx1): s = 'cyan_stained_glass'
                    cv.set(x, y, z, s)
                else: cv.set(x, y, z, None)
    for y in range(1, 5):
        for x in (-1, 0, 1): cv.set(x, y, hz1, None)
    PT.roof_gable(cv, hx0, hx1, hz0, hz1, 12, 'prismarine_brick_stairs', 'dark_prismarine', trim='dark_prismarine', axis='x')
    for dx in (hx0, hx1):
        castle_tower(cv, dx, 0, hz1, 17, 2, 'dark_prismarine', wall='stone_bricks')
        castle_tower(cv, dx, 0, hz0, 15, 2, 'dark_prismarine', wall='stone_bricks')
    # BED WARS in big block letters over the door, each letter a team colour
    block_text(cv, -15, 6, hz1 + 1, 'BED WARS', ['red', 'blue', 'lime', 'yellow', 'cyan', 'white', 'pink'])
    cv.set(0, 4, hz1 + 1, 'lantern[hanging=true]') if False else None
    hall_inside(cv, hx0, hx1, hz0, hz1)
    # path from the plaza to the hall
    for z in range(hz1 + 1, -13):
        for x in (-2, -1, 0, 1, 2): cv.set(x, 0, z, 'stone_bricks' if abs(x) < 2 else 'polished_andesite')
    # ten gates in an arc around the plaza (south, east and west), first map on the west, last on the east
    pads = []
    n = len(map_themes)
    for i, mt in enumerate(map_themes):
        a = math.radians(-200 + 220 * i / (n - 1)) if False else math.radians(180 - 360 * 0.0)
        a = math.radians(200 - 220 * i / (n - 1))           # 200 deg (west-north-west) ... -20 deg (east-north-east), through south
        r = 27
        gx, gz = round(r * math.cos(a)), round(r * math.sin(a))
        # path
        for t in range(14, r - 1):
            for w in (-1, 0, 1):
                px = round(t * math.cos(a) - w * math.sin(a)); pz = round(t * math.sin(a) + w * math.cos(a))
                cv.set(px, 0, pz, 'gravel' if w else 'dirt_path')
                for y in (1, 2): cv.set(px, y, pz, None)
        cells = gate(cv, gx, gz, a, mt, i)
        pads.append(dict(id=mt['id'], cells=cells))
        # a signpost beside the arch, facing the plaza
        ux, uz = -math.sin(a), math.cos(a)
        px, pz = round(gx + ux * 4 - math.cos(a) * 1), round(gz + uz * 4 - math.sin(a) * 1)
        cv.set(px, 0, pz, 'polished_andesite'); cv.set(px, 1, pz, 'dark_oak_fence')
        yaw = math.degrees(math.atan2(math.cos(a), -math.sin(a)))      # direction to the plaza as a sign rotation
        rot = round(((math.degrees(math.atan2(math.cos(a), -(math.sin(a)))) ) % 360) / 22.5)
        fx, fz = -math.cos(a), -math.sin(a)                                 # facing the plaza
        rot = round((math.degrees(math.atan2(-fx, fz)) % 360) / 22.5) % 16
        sign(cv, px, 2, pz, [(f"{i + 1}. {mt['name']}", 'gold'), (f"{mt.get('size', '?')}x{mt.get('size', '?')}", 'white'), ('8팀', 'white'), ('▶ 들어가기', 'aqua')], rotation=rot)
    # trees and flowers round the outside
    rng = cv.rng
    for k in range(40):
        a = rng.random() * 2 * math.pi; r = rng.uniform(35, 52)
        x, z = round(r * math.cos(a) * RX / 58), round(r * math.sin(a) * RZ / 54)
        if (x, z) not in hm or (hx0 - 4 <= x <= hx1 + 4 and hz0 - 4 <= z <= hz1 + 4): continue
        y = hm[(x, z)]
        kind = k % 4
        if kind == 0: PT.big_oak(cv, x, y + 1, z, 8, 'oak_log', 'oak_leaves', 4.5, seed + k)
        elif kind == 1: PT.cherry(cv, x, y + 1, z, 5, 3.6, seed + k)
        elif kind == 2: PT.oak(cv, x, y + 1, z, 6, 'birch_log', 'birch_leaves', 2.8, seed + k)
        else: PT.spruce(cv, x, y + 1, z, 10, 'spruce_log', 'spruce_leaves', 3)
    PT.flora(cv, hm, th, 0.25, avoid=lambda x, z: math.hypot(x, z) < 30)
    # showpiece islands round the lobby
    shows = [(90, giant_bed), (150, giant_tnt), (210, giant_sword), (270, None), (330, 'diamond'), (30, 'emerald')]
    for k, (deg, fn) in enumerate(shows):
        if fn is None: continue
        a = math.radians(deg); r = 90
        sx, sz = round(r * math.cos(a)), round(r * math.sin(a))
        sub = Canvas(seed + 50 + k)
        shm = PT.island(sub, 0, 0, 0, 10, 9, 18, th, seed + 50 + k, flat=0.5, hill=1.6)
        if fn == giant_bed: giant_bed(sub, 0, 3, 0)
        elif fn == giant_tnt: giant_tnt(sub, -3, 1, -3, 6)
        elif fn == giant_sword: giant_sword(sub, 0, -2, 0)
        elif fn == 'diamond': giant_gem(sub, 0, 8, 0, 5, 'diamond_block', 'light_blue_stained_glass')
        elif fn == 'emerald': giant_gem(sub, 0, 8, 0, 5, 'emerald_block', 'lime_stained_glass')
        PT.flora(sub, shm, th, 0.3)
        for t in range(3):
            tx, tz = rng.randint(-7, 7), rng.randint(-7, 7)
            if (tx, tz) in shm and abs(tx) + abs(tz) > 6: PT.oak(sub, tx, shm[(tx, tz)] + 1, tz, 5, 'oak_log', 'oak_leaves', 2.4, seed + t)
        cv.paste(sub, sx, 6 + (k % 3) * 4, sz)
    cv.marker(0, 1, 9, ['bw', 'bw.lobby', 'bw.lobby.spawn'])
    return cv, pads

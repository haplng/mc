"""Map 10 - 해적: eight pirate ships close in on skull island; treasure sandbars on the axes carry the diamonds, a kraken lurks in the corners."""
import math
from canvas import Canvas
from kit import *
from m07_turtle import SAND

ID = 'pirate'; NAME = '해적'
GATE = dict(frame='dark_oak_planks', roof_full='spruce_planks', plaza='sand', glass='red_stained_glass')
PROF = {0: 1.0, -1: 1.0, -2: 0.92, -3: 0.78, -4: 0.58, -5: 0.34, -6: 0.12}

def hw(z):
    if z <= -15: return 3.4
    if z <= -12: return 4.3
    if z <= 6: return 5.0
    return max(0.4, 5.0 * (1 - ((z - 6) / 10.6) ** 1.7))

def sail(cv, x0, x1, y0, y1, z, dye, bulge=2.0):
    xc = (x0 + x1) / 2; w = max(1, x1 - x0)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            zo = round(bulge * math.sin(math.pi * (y - y0 + 0.5) / (y1 - y0 + 1)) * (1 - 0.6 * (2 * (x - xc) / w) ** 2))
            cv.set(x, y, z + zo, (dye + '_wool') if (x - x0) % 4 < 2 else ('light_gray_wool' if dye == 'white' else 'white_wool'))

def ship_base(dye):
    cv = Canvas(sum(map(ord, dye)) + 10)
    T = dye + '_concrete'
    cells = set()
    for z in range(-16, 17):
        for y in range(-6, 1):
            w = hw(z) * PROF[y]
            for x in range(-6, 7):
                if abs(x) <= w: cells.add((x, y, z))
    for (x, y, z) in cells:
        skin = any((x + d[0], y + d[1], z + d[2]) not in cells for d in ((1, 0, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))
        if y == 0 and not skin: m = 'spruce_planks' if x % 2 else 'stripped_spruce_wood'
        elif not skin: m = 'spruce_planks'
        else: m = T if y == 0 else ('dark_oak_planks' if y in (-1, -4, -5, -6) else 'spruce_planks')
        cv.set(x, y, z, m)
    outline = {(x, z) for (x, y, z) in cells if y == 0 and any((x + dx, 0, z + dz) not in cells for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    for (x, z) in outline:
        if z < 15: cv.set(x, 1, z, 'dark_oak_planks')
    for z in (-4, 1, 6):                                                # gun ports
        for sx in (-1, 1):
            cv.set(sx * 5, -1, z, 'black_concrete'); cv.set(sx * 6, -1, z, 'polished_blackstone')
    for z in range(-16, 17): cv.set(0, -7, z, 'dark_oak_log[axis=z]') if abs(z) < 14 else None
    # stern castle: the captain's cabin under the quarterdeck
    deck = {(x, z) for (x, y, z) in cells if y == 0}
    for (x, z) in deck:
        if z > -8: continue
        wall = (x, z) in outline or z == -8
        if wall:
            for y in range(1, 5): cv.set(x, y, z, 'dark_oak_planks' if (y == 4 or abs(x) == 5 and z == -8) else 'spruce_planks')
        cv.set(x, 5, z, 'spruce_planks' if x % 2 else 'stripped_spruce_wood')
        if (x, z) in outline or (z == -8 and abs(x) != 4): cv.set(x, 6, z, 'dark_oak_fence')
    for y in (1, 2): cv.set(0, y, -8, None)
    cv.set(0, 6, -8, 'dark_oak_fence')
    for x in (-3, 3): cv.set(x, 2, -8, 'glass_pane'); cv.set(x, 3, -8, 'glass_pane')
    for x in (-2, -1, 1, 2):
        for y in (2, 3): cv.set(x, y, -16, 'glass_pane')
    for sx in (-1, 1):
        for z in (-12, -11):
            x = sx * 4 if (sx * 4, z) in outline else sx * 5
            if (x, z) in outline: cv.set(x, 2, z, 'glass_pane')
        for y in range(1, 6): cv.set(sx * 4, y, -7, 'ladder[facing=south]')
        cv.set(sx * 3, 7, -16, 'dark_oak_fence'); cv.set(sx * 3, 8, -16, 'lantern[hanging=false]')
    cv.set(-3, 1, -7, 'chest[facing=south]'); cv.set(3, 1, -7, 'ender_chest[facing=south]')
    # cabin furniture
    cv.set(0, 1, -13, 'spruce_fence'); cv.set(0, 2, -13, 'spruce_pressure_plate'); cv.set(-1, 1, -13, 'cartography_table'); cv.set(0, 1, -14, 'spruce_stairs[facing=south,half=bottom]')
    cv.set(2, 1, -14, 'barrel[facing=up]'); cv.set(-2, 1, -14, 'bookshelf'); cv.set(-2, 2, -14, 'bookshelf'); cv.set(2, 2, -14, 'lantern[hanging=false]')
    cv.set(-3, 1, -10, 'barrel[facing=up]'); cv.set(3, 1, -10, 'gold_block'); cv.set(3, 1, -11, 'raw_gold_block'); hang_lamp(cv, 0, 4, -11)
    for z in (-12, -11, -10): cv.set(0, 1, z, 'red_carpet'); cv.set(1, 1, z, 'red_carpet') if z != -12 else None
    # quarterdeck: wheel, mizzen with a lateen sail
    cv.set(0, 6, -10, 'dark_oak_fence'); cv.set(0, 7, -10, 'spruce_trapdoor[facing=south,half=bottom,open=true]')
    for y in range(6, 17): cv.set(0, y, -13, 'spruce_log[axis=y]')
    for i in range(8):                                                  # lateen sail: a triangle behind the mizzen
        for y in range(8 + i, 16 - i): cv.set(0, y, -12 + i, dye + '_wool')
    flag(cv, 0, 17, -13, 3, dye, d=(0, -1), pole='spruce_fence', w=3, hh=2)
    # main mast, yards, sails, top
    for y in range(1, 25): cv.set(0, y, 2, 'spruce_log[axis=y]')
    for x in range(-6, 7): cv.set(x, 16, 2, 'stripped_spruce_wood[axis=x]'); cv.set(x, 8, 2, 'stripped_spruce_wood[axis=x]') 
    for x in range(-4, 5): cv.set(x, 23, 2, 'stripped_spruce_wood[axis=x]')
    sail(cv, -6, 6, 9, 15, 3, dye, 2.2); sail(cv, -4, 4, 17, 22, 3, dye, 1.6)
    disc(cv, 0, 24, 2, 1.6, 'spruce_planks'); flag(cv, 0, 25, 2, 4, dye, d=(0, -1), pole='spruce_fence')
    line(cv, (0, 1, 15), (0, 4, 21), 'stripped_spruce_wood[axis=z]'); cv.set(0, 0, 17, 'gold_block')
    # deck
    gen_pad(cv, 0, 0, -4, 'iron', frame='spruce_planks')
    cv.set(-4, 1, 4, 'barrel[facing=up]'); cv.set(-4, 2, 4, 'lantern[hanging=false]'); cv.set(4, 1, 4, 'barrel[facing=up]'); cv.set(4, 1, 5, 'barrel[facing=up]'); cv.set(4, 2, 4, 'lantern[hanging=false]')
    cv.set(-4, 1, 5, 'smithing_table') if False else cv.set(-4, 1, 5, 'crafting_table')
    bed(cv, dye, 0, 1, 9)
    team_markers(cv, dye, spawn=(0, 1, -1), bedpos=(0, 1, 9), gen=(0, 0, -4), shop=(-3, 1, 5), upg=(3, 1, 5))
    return cv

def skull_island():
    cv = Canvas(110)
    nz = cv.noise
    th = dict(SAND); th['top'] = lambda x, y, z: 'sand' if math.hypot(x, z) + (nz.f2(x, z, 8.0) - 0.5) * 8 > 27 else ('grass_block' if nz.n2(x + 5, z + 5, 4.0) > 0.25 else 'moss_block')
    hm = island(cv, 0, 0, 0, (38, 38), 22, th, seed=6, flat=0.8, hill=1.8, rough=0.18)
    # the skull
    BONE = [('calcite', 3), ('white_concrete', 2), ('diorite', 2), ('bone_block', 2), ('smooth_quartz', 1)]
    ellipsoid(cv, 0, 9, -2, 11, 10, 12, BONE)
    ellipsoid(cv, 0, 2, 4, 7.5, 3.5, 7, BONE)                           # jaw
    ellipsoid(cv, 0, 6, -2, 7.5, 5, 9, None) if False else None
    for x in range(-8, 9):                                              # hollow it out: the treasure cave
        for y in range(1, 9):
            for z in range(-11, 8):
                if (x / 7.6) ** 2 + ((y - 3) / 5.6) ** 2 + ((z + 2) / 9.2) ** 2 < 1: cv.set(x, y, z, None)
    for x in range(-3, 4):                                              # the mouth
        for y in range(1, 5):
            for z in range(6, 13):
                if abs(x) <= 3 - (1 if y == 4 else 0): cv.set(x, y, z, None)
    for x in (-3, -1, 1, 3): cv.set(x, 4, 10, 'smooth_quartz'); cv.set(x, 3, 10, 'smooth_quartz') if abs(x) == 3 else None
    for sx in (-1, 1):                                                  # eyes, nose
        for x in range(-12, 13):
            for y in range(6, 18):
                for z in range(2, 12):
                    if (x - sx * 4.6) ** 2 + (y - 11.5) ** 2 + (z - 8.6) ** 2 < 3.3 ** 2 and cv.get(x, y, z): cv.set(x, y, z, 'black_concrete' if z < 7 else None)
        cv.set(sx * 5, 11, 6, 'shroomlight'); cv.set(sx * 4, 11, 6, 'shroomlight')
    for (x, y) in ((0, 8), (0, 7), (-1, 6), (0, 6), (1, 6)):
        for z in (9, 10, 11): cv.set(x, y, z, None)
        cv.set(x, y, 8, 'black_concrete')
    for i in range(40):                                                 # moss and cracks
        x, y, z = cv.rng.randint(-11, 11), cv.rng.randint(1, 8), cv.rng.randint(-13, 10)
        if cv.get(x, y, z) and cv.name(x, y, z) in ('calcite', 'diorite', 'white_concrete', 'bone_block'): cv.set(x, y, z, cv.rng.choice(('mossy_cobblestone', 'andesite', 'moss_block')))
    # treasure
    for x in range(-6, 7):
        for z in range(-9, 6):
            if hm.get((x, z)) is not None and cv.empty(x, 1, z) and cv.get(x, 0, z): cv.set(x, 0, z, cv.pick([('sand', 3), ('coarse_dirt', 2), ('gravel', 1)]))
    for (x, z, s) in ((-4, -6, 'gold_block'), (-3, -6, 'gold_block'), (-4, -5, 'raw_gold_block'), (-4, -7, 'barrel[facing=up]'), (4, -6, 'barrel[facing=up]'), (5, -5, 'raw_gold_block'),
                      (4, -7, 'gold_block'), (0, -9, 'barrel[facing=south]'), (-5, 0, 'skeleton_skull[rotation=4]'), (5, 1, 'emerald_block'), (3, -8, 'lantern[hanging=false]'), (-3, -8, 'lantern[hanging=false]')):
        if cv.empty(x, 1, z) and cv.get(x, 0, z): cv.set(x, 1, z, s)
    cv.set(-4, 2, -6, 'gold_block'); cv.set(4, 2, -7, 'lantern[hanging=false]')
    # jungle
    for a in range(0, 360, 30):
        r = 22 + cv.rng.randint(-3, 9); x, z = round(r * math.cos(math.radians(a + 10))), round(r * math.sin(math.radians(a + 10)))
        y = hm.get((x, z))
        if y is not None and cv.empty(x, y + 1, z) and abs(abs(a + 10) % 90 - 45) > 12: palm(cv, x, y + 1, z, cv.rng.randint(6, 10), lean=(1 if x > 0 else -1, 0))
    flora(cv, hm, [('fern', 3), ('short_grass', 4), ('large_fern|tall', 1), ('poppy', 0.5)], 0.22, on=('grass_block', 'moss_block'))
    for i in range(9):
        a = cv.rng.uniform(0, 360); r = cv.rng.uniform(14, 24); x, z = round(r * math.cos(math.radians(a))), round(r * math.sin(math.radians(a)))
        y = hm.get((x, z))
        if y is not None and cv.name(x, y, z) in ('grass_block', 'moss_block') and abs(abs(a) % 90 - 45) > 14: blob(cv, x, y + 1, z, 2.2, 1.5, 2.2, ['jungle_leaves'], seed=i)
    # four piers on the axes, emeralds on the diagonals
    for k in range(4):
        for d in range(30, 53):
            for w in (-1, 0, 1):
                x, z = rot_xz(d, w, k)
                if cv.empty(x, 0, z) and cv.empty(x, 1, z): cv.set(x, 0, z, 'spruce_planks' if w == 0 else 'stripped_spruce_wood')
            if d % 5 == 0 and d > 36:
                for w in (-1, 1):
                    x, z = rot_xz(d, w, k)
                    for y in range(-1, -5, -1):
                        if cv.empty(x, y, z): cv.set(x, y, z, 'spruce_fence')
        for w in (-1, 1):
            x, z = rot_xz(52, w, k); cv.set(x, 1, z, 'spruce_fence'); cv.set(x, 2, z, 'lantern[hanging=false]')
        x, z = rot_xz(17, 17, k)
        flatten(cv, hm, x - 2, z - 2, x + 2, z + 2, 0, th, top='sandstone')
        gen_pad(cv, x, 0, z, 'emerald', frame='smooth_sandstone'); gem_marker(cv, x, 0, z, 'emerald')
    return cv

def sandbar(i):
    cv = Canvas(115 + i)
    hm = island(cv, 0, 0, 0, (10.5, 10.5), 10, SAND, seed=50 + i, flat=0.85, hill=1.0, rough=0.15)
    gen_pad(cv, 0, 0, 0, 'diamond', frame='smooth_sandstone'); gem_marker(cv, 0, 0, 0, 'diamond')
    for d in range(-2, 3):                                              # X marks the spot
        for (x, z) in ((-5 + d, 4 + d), (-5 + d, 4 - d)):
            if hm.get((x, z)) == 0: cv.set(x, 0, z, 'red_concrete')
    if hm.get((5, -4)) is not None: palm(cv, 5, hm[(5, -4)] + 1, -4, 7, lean=(1, 0))
    for (x, z, s) in ((4, 5, 'barrel[facing=up]'), (5, 5, 'barrel[facing=east]'), (-6, -3, 'spruce_fence')):
        if hm.get((x, z)) == 0 and cv.empty(x, 1, z): cv.set(x, 1, z, s)
    return cv

def tentacles(i):
    cv = Canvas(120 + i)
    M1 = [('magenta_concrete', 3), ('purple_concrete', 2), ('magenta_terracotta', 1)]
    curve(cv, [(0, -24, 0), (2, -10, 1), (-3, 2, 3), (-6, 12, 0), (-2, 19, -4), (4, 17, -6)], M1, taper=(3.4, 0.8))
    curve(cv, [(9, -24, -7), (10, -12, -9), (13, -2, -7), (15, 6, -11), (11, 10, -14)], M1, taper=(2.6, 0.7))
    for (x, y, z), s in list(cv.b.items()):
        if cv.rng.random() < 0.05: cv.set(x, y, z, 'pink_concrete')
    return cv

def flotsam(i):
    cv = Canvas(125 + i)
    if i % 2 == 0:
        for z in range(-2, 3): vdisc(cv, 0, 0, z, 1.6, 'dark_oak_planks' if z in (-2, 0, 2) else 'spruce_planks', axis='z')
    else:
        box(cv, -1, -1, -1, 1, 1, 1, 'spruce_planks'); box(cv, -1, -1, -1, 1, 1, 1, 'dark_oak_planks', hollow=False) if False else None
        for a in (-1, 1):
            for b in (-1, 1):
                for y in (-1, 0, 1): cv.set(a, y, b, 'dark_oak_planks')
    return cv

def build():
    mb = MapBuilder(1010)
    mb.put(skull_island(), 0, 0, kind='mid')
    mb.bases(ship_base, 120.6, 14)
    for k in range(4):
        x, z = rot_xz(78, 0, k); mb.put(sandbar(k), x, z, kind='diamond')
        x, z = rot_xz(64, 64, k); mb.put(tentacles(k), x, z, k=k, kind='extra')
        for j, (d, w) in enumerate(((63, 12), (64, -11))):
            x, z = rot_xz(d, w, k); mb.put(flotsam(k * 2 + j), x, z, y=-1, k=k, kind='rock')
    return mb

"""Map 8 - 풍차: windmills on tulip fields; a canal village in the middle, flower strips on the axes, the diamonds far out in the corners."""
import math
from canvas import Canvas
from kit import *
from m05_stadium import TH

ID = 'windmill'; NAME = '풍차'
GATE = dict(frame='bricks', roof_full='dark_oak_planks', plaza='stone_bricks', glass='orange_stained_glass')
WHITE = [('white_concrete', 6), ('calcite', 2), ('smooth_quartz', 1)]
STONEB = [('stone_bricks', 5), ('cracked_stone_bricks', 1), ('mossy_stone_bricks', 1), ('cobblestone', 1)]
FLOWERS = ['red_tulip', 'orange_tulip', 'pink_tulip', 'white_tulip', 'allium', 'cornflower', 'dandelion', 'azure_bluet']

def windmill(cv, cx, y0, cz, r0, h, sail, dye='white', big=True):
    r_at = lambda i: r0 - r0 * 0.38 * i / (h - 1)
    for i in range(h):
        r = r_at(i); disc(cv, cx, y0 + i, cz, r, STONEB if i < 3 else WHITE, r_in=r - 1)
    rt = r_at(h - 1)
    lathe(cv, cx, y0 + h, cz, [rt + 0.7, rt, max(0.6, rt - 1.3)], 'dark_oak_planks')
    if big:
        for i in range(h): cv.set(cx, y0 + i, cz, 'stripped_spruce_log[axis=y]')
        for fy in (4, 8) + ((12, 16) if h > 16 else ()):
            if fy < h - 1:
                disc(cv, cx, y0 + fy, cz, r_at(fy) - 1, 'spruce_planks'); cv.set(cx, y0 + fy, cz, 'stripped_spruce_log[axis=y]')
        for i in range(h - 1): cv.set(cx, y0 + i, cz + 1, 'ladder[facing=south]')
        g = r_at(4)
        disc(cv, cx, y0 + 4, cz, g + 2, 'spruce_planks', r_in=g - 0.5); disc(cv, cx, y0 + 5, cz, g + 2, 'spruce_fence', r_in=g + 1)
        for x in (-1, 0, 1):
            for y in (0, 1, 2):
                for z in range(int(r0) - 2, int(r0) + 2): cv.set(cx + x, y0 + y, cz + z, None)
        for x in (-2, 2):
            for y in (0, 1, 2): cv.set(cx + x, y0 + y, cz + int(r0), 'spruce_planks', force=False)
        for sx in (-1, 1):
            for wy in (6, 7): cv.set(cx + sx * int(r_at(wy) + 0.4), y0 + wy, cz, 'glass')
            for wy in (0, 1, 2): pass
        # gallery door
        for y in (5, 6): cv.set(cx, y0 + y, cz + int(r_at(5) + 0.4), None)
    else:
        cv.set(cx, y0, cz + int(r0), None); cv.set(cx, y0 + 1, cz + int(r0), None)
    hy = y0 + h - 2; hz = cz + int(r_at(h - 2)) + 2
    for z in range(cz + 1, hz + 1): cv.set(cx, hy, z, 'dark_oak_log[axis=z]')
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        ox, oy = (-sy, 0) if sx * sy > 0 else (0, sx)
        for i in range(1, sail + 1):
            cv.set(cx + sx * i, hy + sy * i, hz, 'dark_oak_planks')
            if i >= 2:
                for j in (1, 2) if sail > 5 else (1,):
                    cv.set(cx + sx * i + ox * j, hy + sy * i + oy * j, hz, (dye + '_wool') if (i + j) % 3 else 'white_wool')

def mill_base(dye):
    cv = Canvas(sum(map(ord, dye)) + 8)
    hm = island(cv, 0, 0, 0, squircle(13.5, 15.5, 4), 12, TH, seed=8, flat=0.92, hill=1.0, rough=0.08, ext=(14, 16))
    windmill(cv, 0, 1, -7, 5.5, 13, 8, dye)
    # ground floor of the mill: millstones and sacks
    for (x, z, s) in ((-3, -8, 'smooth_stone_slab[type=bottom]'), (-3, -9, 'grindstone[face=floor,facing=north]'), (3, -8, 'barrel[facing=up]'), (3, -9, 'hay_block[axis=y]'),
                      (2, -10, 'white_wool'), (-2, -10, 'barrel[facing=up]'), (3, -6, 'composter')):
        cv.set(x, 1, z, s)
    cv.set(-3, 2, -8, 'smooth_stone_slab[type=bottom]'); hang_lamp(cv, 2, 4, -6); hang_lamp(cv, -2, 4, -6)
    cv.set(-2, 6, -8, 'bookshelf'); cv.set(2, 6, -8, 'crafting_table'); cv.set(-2, 6, -5, dye + '_carpet'); cv.set(2, 6, -5, 'lantern[hanging=false]')
    # yard: path, generator, chests, tulip rows
    for z in range(-1, 14):
        for x in (-1, 0, 1):
            if (x, z) in hm and hm[(x, z)] == 0: cv.set(x, 0, z, cv.pick([('cobblestone', 3), ('gravel', 0), ('stone_bricks', 2), ('mossy_cobblestone', 1)]))
    gen_pad(cv, 0, 0, 3, 'iron', frame='stone_bricks')
    cv.set(-3, 1, 0, 'chest[facing=south]'); cv.set(3, 1, 0, 'ender_chest[facing=south]')
    for x in range(-12, 13):
        for z in range(5, 14):
            if abs(x) < 4 or (x, z) not in hm or hm[(x, z)] != 0 or not cv.empty(x, 1, z) or cv.name(x, 0, z) != 'grass_block': continue
            if abs(x) % 2 == 0: cv.set(x, 1, z, FLOWERS[(abs(x) // 2) % 4])
    for (x, z) in ((-10, -3), (10, -4), (-11, 1), (9, -9), (-9, -10)):
        if hm.get((x, z)) is not None and cv.empty(x, hm[(x, z)] + 1, z) and cv.name(x, hm[(x, z)], z) == 'grass_block': cv.set(x, hm[(x, z)] + 1, z, 'short_grass')
    stall(cv, -8, 1, 2, 3, 'white', dye); stall(cv, 8, 1, 2, 1, 'white', dye)
    for x in (-9, -8, -7, 7, 8, 9):
        for z in (1, 2, 3): cv.set(x, 0, z, 'stone_bricks') if (x, z) in hm else None
    bed(cv, dye, 0, 1, 9)
    team_markers(cv, dye, spawn=(0, 1, 6), bedpos=(0, 1, 9), gen=(0, 0, 3), shop=(-8, 1, 2), upg=(8, 1, 2))
    return cv

def canal_house(i):
    """a narrow gabled house; its front looks to local -z"""
    cv = Canvas(81 + i)
    wall = ([('bricks', 6), ('granite', 1)], [('mud_bricks', 5), ('packed_mud', 1)], [('orange_terracotta', 5), ('terracotta', 1)], [('bricks', 3), ('polished_granite', 2)])[i % 4]
    box(cv, -3, 1, -4, 3, 12, 4, wall, hollow=True); box(cv, -2, 1, -3, 2, 12, 3, None)
    box(cv, -3, 0, -4, 3, 0, 4, 'spruce_planks'); box(cv, -2, 5, -3, 2, 5, 3, 'spruce_planks'); box(cv, -2, 9, -3, 2, 9, 3, 'spruce_planks')
    for z in (-4, 4):                                                   # stepped gables
        for j, hw in enumerate((3, 2, 1, 0)):
            for x in range(-3, 4):
                if abs(x) > hw: cv.set(x, 10 + j, z, None)
                elif abs(x) == hw: cv.set(x, 10 + j, z, 'smooth_quartz')
        cv.set(0, 14, z, 'smooth_quartz')
    for j in range(3):                                                  # roof
        for z in range(-3, 4):
            cv.set(-3 + j, 10 + j, z, 'dark_oak_stairs[facing=east,half=bottom]'); cv.set(3 - j, 10 + j, z, 'dark_oak_stairs[facing=west,half=bottom]')
            for x in range(-3, 4):
                if abs(x) > 3 - j: cv.set(x, 10 + j, z, None)
    for z in range(-3, 4): cv.set(0, 13, z, 'dark_oak_slab[type=bottom]')
    for y in (10, 11, 12):
        for z in range(-3, 4):
            for x in (-3, 3): cv.set(x, y, z, None) if cv.name(x, y, z) not in ('dark_oak_stairs',) else None
    for y in (1, 2): cv.set(0, y, -4, None)
    cv.set(0, 3, -4, 'smooth_quartz')
    for fy in (2, 6):
        for x in (-2, 2):
            cv.set(x, fy, -4, 'glass'); cv.set(x, fy + 1, -4, 'glass') if fy > 2 else None
        for z in (-1, 1): cv.set(-3, fy + (0 if fy > 2 else 0), z, 'glass'); cv.set(3, fy, z, 'glass')
    cv.set(0, 7, -4, 'glass'); cv.set(0, 11, -4, 'glass'); cv.set(0, 7, 4, 'glass')
    # shop on the ground floor, a living room above, ladder between them
    for x in (-2, -1, 1, 2): cv.set(x, 1, 1, 'barrel[facing=up]')
    cv.set(-2, 1, 3, 'bookshelf'); cv.set(-2, 2, 3, 'bookshelf'); cv.set(0, 1, 3, 'honeycomb_block'); cv.set(1, 1, 3, 'honeycomb_block'); cv.set(1, 2, 3, 'honeycomb_block')
    cv.set(0, 4, 0, 'lantern[hanging=true]'); cv.set(-1, 2, 1, 'flower_pot'); cv.set(-2, 1, -2, 'orange_carpet'); cv.set(-1, 1, -2, 'orange_carpet')
    for y in range(1, 10): cv.set(2, y, 3, 'ladder[facing=north]')
    table(cv, -1, 6, 0, 'spruce', chairs=((0, 1), (0, -1))); cv.set(-2, 6, 3, 'bookshelf'); cv.set(-1, 6, 3, 'cartography_table'); cv.set(0, 8, -1, 'lantern[hanging=true]')
    cv.set(-2, 10, 3, 'barrel[facing=up]'); cv.set(-2, 10, -2, 'hay_block[axis=y]'); cv.set(0, 10, 0, 'red_carpet')
    return cv

def village():
    cv = Canvas(88)
    hm = island(cv, 0, 0, 0, squircle(33, 33, 3), 18, TH, seed=4, flat=0.86, hill=1.4, rough=0.1, ext=(34, 34))
    pave = [('stone_bricks', 4), ('cobblestone', 2), ('andesite', 1), ('mossy_cobblestone', 1)]
    for x in range(-27, 28):
        for z in range(-27, 28):
            r = math.hypot(x, z)
            if hm.get((x, z)) != 0: continue
            if 12.5 <= r < 15.5:
                cv.set(x, 0, z, 'water')
            elif 11.5 <= r < 12.5 or 15.5 <= r < 16.5: cv.set(x, 0, z, 'stone_bricks')
            elif r < 11.5: cv.set(x, 0, z, cv.pick(pave)) if r >= 8 else None
            elif r < 26 and (abs(x) <= 2 or abs(z) <= 2 or 16.5 <= r < 19): cv.set(x, 0, z, cv.pick(pave))
    for k in range(4):
        for d in range(12, 17):
            for w in (-2, -1, 0, 1, 2):
                x, z = rot_xz(d, w, k); cv.set(x, 0, z, 'spruce_planks' if abs(w) < 2 else 'stripped_spruce_wood')
        for d in (12, 16):
            for w in (-2, 2):
                x, z = rot_xz(d, w, k); cv.set(x, 1, z, 'spruce_fence'); cv.set(x, 2, z, 'lantern[hanging=false]') if d == 16 else None
        x, z = rot_xz(23, 0, k); gen_pad(cv, x, 0, z, 'emerald', frame='stone_bricks'); gem_marker(cv, x, 0, z, 'emerald')
        x, z = rot_xz(20, 20, k)
        box(cv, x - 3, -1, z - 4, x + 3, 0, z + 4, 'stone_bricks') if k % 2 == 0 else box(cv, x - 4, -1, z - 3, x + 4, 0, z + 3, 'stone_bricks')
        cv.paste(canal_house(k), x, 0, z, k=(k + 2) % 4 if False else k)
        # cheese stacks and flower tubs by the houses
        x, z = rot_xz(22, 9, k); cv.set(x, 1, z, 'honeycomb_block'); cv.set(x, 2, z, 'honeycomb_block'); cv.set(x + 1, 1, z, 'honeycomb_block')
        x, z = rot_xz(9, 22, k)
        if hm.get((x, z)) == 0 and cv.name(x, 0, z) == 'grass_block': cv.set(x, 1, z, 'red_tulip')
    windmill(cv, 0, 1, 0, 7.5, 20, 12, 'white')
    for (x, z, s) in ((-4, -3, 'barrel[facing=up]'), (-4, -2, 'barrel[facing=up]'), (4, -3, 'hay_block[axis=y]'), (4, -2, 'hay_block[axis=y]'), (4, -2, None),
                      (-3, -5, 'smooth_stone_slab[type=bottom]'), (3, -5, 'grindstone[face=floor,facing=north]'), (0, -5, 'chest[facing=south]')):
        if s: cv.set(x, 1, z, s)
    for a in range(0, 360, 30):                                         # tulips round the outside
        for r in (27, 29):
            x, z = round(r * math.cos(math.radians(a + 15))), round(r * math.sin(math.radians(a + 15)))
            y = hm.get((x, z))
            if y is not None and cv.name(x, y, z) == 'grass_block' and cv.empty(x, y + 1, z): cv.set(x, y + 1, z, FLOWERS[(a // 30) % 8])
    return cv

def strip(i):
    """a field of flowers in stripes; long side along local z"""
    cv = Canvas(84 + i)
    hm = island(cv, 0, 0, 0, squircle(8.5, 14.5, 5), 10, TH, seed=30 + i, flat=1.2, rough=0.05, ext=(9, 15))
    for (x, z), y in hm.items():
        if abs(z) <= 1: cv.set(x, 0, z, cv.pick([('dirt_path', 4), ('coarse_dirt', 1)])) if False else cv.set(x, 0, z, 'coarse_dirt')
        elif abs(x) <= 7 and cv.name(x, 0, z) == 'grass_block' and (z + 30) % 3 != 2: cv.set(x, 1, z, FLOWERS[((z + 30) // 3) % 8])
    for sz in (-1, 1):
        for y in (1, 2): cv.set(0, y, sz * 13, 'oak_fence')
        cv.set(0, 3, sz * 13, 'carved_pumpkin[facing=%s]' % ('north' if sz < 0 else 'south')); cv.set(0, 4, sz * 13, 'hay_block[axis=y]') if False else None
    return cv

def polder(i):
    cv = Canvas(86 + i)
    hm = island(cv, 0, 0, 0, (11.5, 11.5), 11, TH, seed=40 + i, flat=0.8, hill=1.2, rough=0.14)
    windmill(cv, 4, 1, 4, 3.2, 9, 5, 'white', big=False)
    gen_pad(cv, -2, 0, -2, 'diamond', frame='stone_bricks'); gem_marker(cv, -2, 0, -2, 'diamond')
    for (x, z) in ((-6, 3), (-5, 3), (-6, 4), (3, -6)):
        if hm.get((x, z)) == 0: cv.set(x, 1, z, 'hay_block[axis=y]')
    cv.set(-6, 2, 3, 'hay_block[axis=y]') if hm.get((-6, 3)) == 0 else None
    for a in range(0, 360, 40):
        x, z = round(8 * math.cos(math.radians(a))), round(8 * math.sin(math.radians(a)))
        y = hm.get((x, z))
        if y is not None and cv.name(x, y, z) == 'grass_block' and cv.empty(x, y + 1, z): cv.set(x, y + 1, z, FLOWERS[(a // 40) % 8])
    return cv

def build():
    mb = MapBuilder(808)
    mb.put(village(), 0, 0, kind='mid')
    spots = []
    for q in range(4):
        for sgn in (-1, 1):
            x, z = rot_xz(105, sgn * 38, q); spots.append((x, z, (q + 1) % 4, sgn > 0))
    mb.bases_at(mill_base, spots)
    for k in range(4):
        x, z = rot_xz(62, 0, k); mb.put(strip(k), x, z, k=k, kind='extra')
        x, z = rot_xz(86, 86, k); mb.put(polder(k), x, z, k=k, kind='diamond')
    return mb

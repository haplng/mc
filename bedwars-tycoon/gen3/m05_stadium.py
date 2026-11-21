"""Map 5 - 축구장: two rows of four grandstands along the touchlines of a football pitch; floodlight corners carry the diamonds."""
import math
from canvas import Canvas
from kit import *

ID = 'stadium'; NAME = '축구장'
GATE = dict(frame='smooth_stone', roof_full='lime_concrete', plaza='moss_block', glass='lime_stained_glass')
TH = dict(top='grass_block', sub=[('dirt', 3), ('coarse_dirt', 1)], under=[('stone', 5), ('andesite', 2), ('tuff', 1), ('cobblestone', 1)],
          tip=[('cobbled_deepslate', 2), ('deepslate', 1), ('tuff', 1)], strata=['stone', 'stone', 'andesite', 'stone', 'tuff', 'cobblestone'])
turf = lambda x, y, z: 'grass_block' if (x // 4) % 2 == 0 else 'moss_block'

def ball(cv, x, y, z, r):
    def m(px, py, pz):
        v = (px - x, py - y, pz - z); n = math.sqrt(sum(c * c for c in v)) or 1; v = [c / n for c in v]
        for c in ((0, 1, 0), (0, -1, 0), (0.89, 0.45, 0), (-0.89, -0.45, 0), (0.28, 0.45, 0.85), (-0.28, -0.45, -0.85), (-0.72, 0.45, 0.53),
                  (0.72, -0.45, -0.53), (-0.72, 0.45, -0.53), (0.72, -0.45, 0.53), (0.28, 0.45, -0.85), (-0.28, -0.45, 0.85)):
            if sum(a * b for a, b in zip(v, c)) > 0.93: return 'black_concrete'
        return 'white_concrete'
    sphere(cv, x, y, z, r, m)

def stand_base(dye):
    cv = Canvas(sum(map(ord, dye)) + 5)
    T = dye + '_concrete'; S = [('smooth_stone', 5), ('stone_bricks', 1)]
    island(cv, 0, 0, 0, squircle(13.5, 15.5, 8), 11, TH, seed=5, flat=1.3, rough=0.03, ext=(14, 16), top=turf)
    # terraces: five tiers, seats are carpets
    for i in range(5):
        for j, z in enumerate((-4 - 2 * i, -5 - 2 * i)):
            for x in range(-12, 13):
                for y in range(1, i + 2): cv.set(x, y, z, cv.pick(S))
                if j == 1 and abs(x) not in (6, 12) and abs(x) > 2: cv.set(x, i + 2, z, dye + '_carpet')
        for x in (-6, 6): cv.set(x, i + 1, -4 - 2 * i, 'stone_brick_stairs[facing=north,half=bottom]')
    box(cv, -12, 1, -14, 12, 9, -14, 'stone_bricks'); box(cv, -12, 6, -14, 12, 7, -14, T)
    for x in (-12, -6, 0, 6, 12): box(cv, x, 1, -14, x, 9, -14, 'polished_andesite')
    box(cv, -12, 10, -14, 12, 10, -7, 'light_gray_concrete'); box(cv, -12, 10, -7, 12, 10, -7, dye + '_wool')
    for x in (-12, -6, 0, 6, 12):
        for z in (-13, -12): cv.set(x, 9, z, 'polished_andesite')
        cv.set(x, 9, -8, 'sea_lantern')
    for x in (-12, 12): flag(cv, x, 11, -14, 4, dye, d=(1 if x < 0 else -1, 0), pole='spruce_fence')
    # players' tunnel and the locker room under the upper tiers
    box(cv, -1, 1, -9, 1, 3, -4, None); box(cv, -10, 1, -13, 10, 3, -10, None)
    box(cv, -11, 0, -13, 11, 0, -10, 'smooth_stone'); box(cv, -1, 0, -9, 1, 0, -4, 'smooth_stone')
    for x in (-2, 2):
        for y in (1, 2, 3): cv.set(x, y, -4, T)
    for x in range(-10, 11, 2):
        if abs(x) > 1: cv.set(x, 1, -13, 'barrel[facing=south]'); cv.set(x, 2, -13, 'barrel[facing=south]')
    for x in (-8, -7, -6, 6, 7, 8): cv.set(x, 1, -10, 'spruce_stairs[facing=south,half=bottom]')
    for x in (-5, 5): hang_lamp(cv, x, 3, -11)
    cv.set(-10, 1, -11, 'cauldron'); cv.set(10, 1, -11, 'crafting_table'); cv.set(0, 1, -13, dye + '_banner[rotation=0]')
    for x in range(-9, 10):
        if cv.empty(x, 1, -12): cv.set(x, 1, -12, dye + '_carpet') if abs(x) % 3 == 0 else None
    # apron
    gen_pad(cv, 0, 0, -1, 'iron', frame='smooth_stone')
    cv.set(-3, 1, -3, 'chest[facing=south]'); cv.set(3, 1, -3, 'ender_chest[facing=south]')
    for sx in (-1, 1):                                                 # dugouts
        for x in range(6, 12):
            cv.set(sx * x, 1, 0, 'spruce_stairs[facing=north,half=bottom]'); cv.set(sx * x, 3, 0, 'light_blue_stained_glass'); cv.set(sx * x, 3, 1, 'light_blue_stained_glass')
            cv.set(sx * x, 0, 0, 'smooth_stone'); cv.set(sx * x, 0, 1, 'smooth_stone')
        for x in (6, 11):
            for y in (1, 2): cv.set(sx * x, y, -1, 'white_concrete')
            cv.set(sx * x, 3, -1, 'white_concrete')
        for x in range(7, 11): cv.set(sx * x, 3, -1, 'white_concrete'); cv.set(sx * x, 1, -1, 'white_concrete'); cv.set(sx * x, 2, -1, 'light_blue_stained_glass')
    for x in range(-6, 7):                                             # goal area lines, goal frame behind the bed
        for z in range(6, 14):
            if (abs(x) == 6 or z == 6) and cv.get(x, 0, z): cv.set(x, 0, z, 'white_concrete')
    for x in (-3, 3):
        for y in (1, 2, 3): cv.set(x, y, 13, 'white_concrete')
    for x in range(-3, 4): cv.set(x, 4, 13, 'white_concrete')
    bed(cv, dye, 0, 1, 10)
    team_markers(cv, dye, spawn=(0, 1, 3), bedpos=(0, 1, 10), gen=(0, 0, -1), shop=(-8, 1, 3), upg=(8, 1, 3))
    return cv

def pitch():
    cv = Canvas(55)
    island(cv, 0, 0, 0, squircle(44, 29, 8), 15, TH, seed=9, flat=1.3, rough=0.03, ext=(45, 30), top=lambda x, y, z: 'grass_block' if (x // 5) % 2 == 0 else 'moss_block')
    Wc = 'white_concrete'
    def ln(x, z):
        if cv.get(x, 0, z): cv.set(x, 0, z, Wc)
    for x in range(-38, 39): ln(x, -23); ln(x, 23)
    for z in range(-23, 24): ln(-38, z); ln(38, z); ln(0, z)
    for a in range(0, 360, 2): ln(round(7 * math.cos(math.radians(a))), round(7 * math.sin(math.radians(a))))
    for sx in (-1, 1):
        for z in range(-11, 12): ln(sx * 27, z)
        for x in range(27, 39): ln(sx * x, -11); ln(sx * x, 11)
        for z in range(-5, 6): ln(sx * 33, z)
        for x in range(33, 39): ln(sx * x, -5); ln(sx * x, 5)
        ln(sx * 30, 0)
        # goal
        for z in (-4, 4):
            for y in (1, 2, 3): cv.set(sx * 39, y, z, Wc)
            for x in (40, 41):
                for y in (1, 2, 3): cv.set(sx * x, y, z, 'iron_bars[east=true,west=true]')
        for z in range(-4, 5):
            cv.set(sx * 39, 4, z, Wc)
            if abs(z) < 4:
                for y in (1, 2, 3): cv.set(sx * 41, y, z, 'iron_bars[north=true,south=true]')
        for z in (-23, 23):                                            # corner flags
            cv.set(sx * 38, 1, z, 'oak_fence'); cv.set(sx * 38, 2, z, 'oak_fence'); cv.set(sx * 38, 3, z, 'orange_wool')
    cols = ('orange', 'magenta', 'light_blue', 'purple', 'brown', 'black')
    for sz in (-1, 1):                                                 # advertising boards along the touchlines
        for x in range(-30, 31):
            if abs(x) < 7 or not cv.get(x, 0, sz * 26): continue
            cv.set(x, 1, sz * 26, cols[((x + 30) // 4) % 6] + '_concrete' if (x + 30) % 4 else 'white_concrete')
    ball(cv, 0, 4, 0, 3)
    for k in range(4):
        x, z = rot_xz(9, 0, k)
        if k % 2: x, z = rot_xz(12, 0, k)
        gen_pad(cv, x, 0, z, 'emerald', frame='white_concrete'); gem_marker(cv, x, 0, z, 'emerald')
    return cv

def corner(i):
    """a floodlight tower; local +z looks at the pitch"""
    cv = Canvas(58 + i)
    island(cv, 0, 0, 0, (7.5, 7.5), 9, TH, seed=20 + i, flat=0.75, hill=1.0, rough=0.12, top=turf)
    gen_pad(cv, 0, 0, 1, 'diamond', frame='smooth_stone'); gem_marker(cv, 0, 0, 1, 'diamond')
    for y in range(1, 15): cv.set(0, y, -4, 'polished_andesite' if y < 3 else 'iron_block')
    for y in range(1, 6):
        for d in (-1, 1): cv.set(d, y, -4, 'iron_bars[east=true,west=true]') if y < 4 else None
    for j, y in enumerate((15, 16, 17)):
        for x in range(-3, 4):
            cv.set(x, y, -4 + (1 if j == 0 else 0), 'ochre_froglight[axis=y]' if (x + j) % 2 == 0 else 'sea_lantern'); cv.set(x, y, -5 + (1 if j == 0 else 0), 'gray_concrete')
    box(cv, -3, 18, -5, 3, 18, -4, 'gray_concrete')
    post_lamp(cv, 4, 1, 3, 'oak_fence', 'lantern', 2)
    return cv

def ball_isle(i):
    cv = Canvas(59 + i); ball(cv, 0, 0, 0, 4.4); return cv

def build():
    mb = MapBuilder(505)
    mb.put(pitch(), 0, 0, kind='mid')
    spots = [(-92, -66, 0, False), (-32, -66, 0, False), (32, -66, 0, True), (92, -66, 0, True),
             (92, 66, 2, False), (32, 66, 2, False), (-32, 66, 2, True), (-92, 66, 2, True)]
    mb.bases_at(stand_base, spots)
    for i, (sx, sz) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        mb.put(corner(i), sx * 62, sz * 33, k=0 if sz < 0 else 2, kind='diamond')
    for i, sx in enumerate((-1, 1)): mb.put(ball_isle(i), sx * 66, 0, y=4, kind='extra')
    return mb

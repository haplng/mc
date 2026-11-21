"""Map 9 - 태양계: ringed planets orbit a glowing sun with a wheel-shaped station; small planets on an inner orbit carry the diamonds."""
import math
from canvas import Canvas
from kit import *

ID = 'solar'; NAME = '태양계'
GATE = dict(frame='smooth_quartz', roof_full='black_concrete', plaza='light_gray_concrete', glass='light_blue_stained_glass')

def planet_base(dye):
    cv = Canvas(sum(map(ord, dye)) + 9)
    T = dye + '_concrete'; Tt = dye + '_terracotta'
    mats = [T, Tt, 'white_terracotta', T, 'light_gray_terracotta', Tt]
    nz = cv.noise
    band = lambda x, y, z: mats[((y + int(3 * nz.n2(x + 40, z + 40, 9.0))) // 2) % len(mats)]
    sphere(cv, 0, -6, 0, 13.5, band, hollow=True, ymax=0); sphere(cv, 0, -6, 0, 12.5, band, hollow=True, ymax=-1)
    disc(cv, 0, 0, 0, 12, lambda x, y, z: T if math.hypot(x, z) >= 10.5 else ('polished_andesite' if (x // 3 + z // 3) % 2 else 'smooth_stone'))
    for x in range(-19, 20):                                            # the ring, tilted sideways
        for z in range(-19, 20):
            r = math.hypot(x, z)
            if 15.5 <= r < 18.6:
                y = -5 + round(0.24 * x)
                cv.set(x, y, z, 'white_concrete' if r < 16.5 else (T if r < 17.6 else 'light_gray_concrete'))
    # habitat dome
    cx, cz = 0, -4
    def glass(x, y, z):
        return 'white_concrete' if (x == cx or z == cz or abs(abs(x - cx) - abs(z - cz)) == 0 and y > 4) else 'light_blue_stained_glass'
    sphere(cv, cx, 0, cz, 6.4, glass, hollow=True, ymin=1)
    for x in (-1, 0, 1):
        for y in (1, 2, 3):
            for z in (1, 2, 3): cv.set(x, y, z, None)
    for x in (-2, 2):
        for y in (1, 2, 3): cv.set(x, y, 2, 'white_concrete')
    for x in range(-2, 3): cv.set(x, 4, 2, 'white_concrete')
    cv.set(cx, 7, cz, 'lightning_rod[facing=up]')
    gen_pad(cv, 0, 0, -5, 'iron', frame='smooth_stone')
    cv.set(-4, 1, -5, 'chest[facing=east]'); cv.set(4, 1, -5, 'ender_chest[facing=west]')
    for (x, z) in ((-3, -8), (3, -8), (-4, -1), (4, -1)): cv.set(x, 0, z, 'sea_lantern')
    cv.set(-2, 1, -8, 'lectern[facing=south]'); cv.set(2, 1, -8, 'observer[facing=south]'); cv.set(0, 1, -9, 'flower_pot'); cv.set(-4, 1, -2, 'potted_fern') if False else None
    cv.set(3, 1, -1, dye + '_carpet'); cv.set(-3, 1, -1, dye + '_carpet')
    # solar panel, rocket
    cv.set(-9, 1, 2, 'iron_bars'); cv.set(-9, 2, 2, 'iron_bars')
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1): cv.set(-9 + dx, 3, 2 + dz, 'daylight_detector')
    rx, rz = 9, 1
    for y in range(2, 8): 
        for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)): cv.set(rx + dx, y, rz + dz, 'white_concrete')
    cv.set(rx, 5, rz + 1, 'light_blue_stained_glass'); cv.set(rx, 8, rz, T); cv.set(rx, 9, rz, T); cv.set(rx, 10, rz, 'end_rod[facing=up]')
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)): cv.set(rx + dx, 8, rz + dz, T)
    for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2)): cv.set(rx + dx, 1, rz + dz, T); cv.set(rx + dx, 2, rz + dz, T)
    cv.set(rx, 1, rz, 'polished_blackstone')
    bed(cv, dye, 0, 1, 8)
    team_markers(cv, dye, spawn=(0, 1, -1), bedpos=(0, 1, 8), gen=(0, 0, -5), shop=(-6, 1, 6), upg=(6, 1, 6))
    return cv

def sun():
    cv = Canvas(91)
    nz = cv.noise
    def fire(x, y, z):
        n = nz.n3(x + 80, y + 80, z + 80, 5.0)
        return 'orange_concrete' if n < 0.36 else 'shroomlight' if n < 0.5 else 'yellow_concrete' if n < 0.68 else 'glowstone' if n < 0.82 else 'ochre_froglight[axis=y]'
    sphere(cv, 0, -10, 0, 19, fire, hollow=True, ymax=0); sphere(cv, 0, -10, 0, 18, fire, hollow=True, ymax=-1)
    disc(cv, 0, 0, 0, 16, lambda x, y, z: 'gold_block' if abs(math.hypot(x, z) - 15.5) < 0.6 else ('yellow_terracotta' if int(math.hypot(x, z)) % 4 == 0 else 'smooth_sandstone'))
    # sun temple
    for a in range(0, 360, 45):
        x, z = round(6 * math.cos(math.radians(a + 22.5))), round(6 * math.sin(math.radians(a + 22.5)))
        for y in range(1, 7): cv.set(x, y, z, 'quartz_pillar[axis=y]')
        cv.set(x, 7, z, 'gold_block')
    disc(cv, 0, 8, 0, 7.5, 'smooth_quartz', r_in=4.5); disc(cv, 0, 9, 0, 5.5, 'smooth_quartz', r_in=2.5); disc(cv, 0, 10, 0, 3, 'yellow_stained_glass')
    cv.set(0, 1, 0, 'gold_block'); cv.set(0, 2, 0, 'beacon'); disc(cv, 0, 0, 0, 2, 'gold_block')
    for k in range(4):
        x, z = rot_xz(11, 0, k); gen_pad(cv, x, 0, z, 'emerald', frame='smooth_sandstone'); gem_marker(cv, x, 0, z, 'emerald')
    for k in range(4):                                                  # prominences
        a = math.radians(45 + 90 * k); ux, uz = math.cos(a), math.sin(a)
        pts = [(15 * ux, -4, 15 * uz), (24 * ux, -1 - k % 2, 24 * uz + 3), (27 * ux + 3 * uz, -8, 27 * uz - 3 * ux), (17 * ux + 5 * uz, -13, 17 * uz - 5 * ux)]
        curve(cv, pts, 'shroomlight', taper=(1.3, 0.5)); curve(cv, [(p[0] * 1.04, p[1] + 1, p[2] * 1.04) for p in pts[:3]], 'orange_stained_glass')
    return cv

def station():
    cv = Canvas(92)
    for x in range(-42, 43):
        for z in range(-42, 43):
            r = math.hypot(x, z)
            if 35.5 <= r < 40.6:
                edge = r < 36.5 or r >= 39.6
                cv.set(x, 0, z, 'iron_block' if edge and (int(math.degrees(math.atan2(z, x)) + 360) // 5) % 2 else ('light_gray_concrete' if edge else 'smooth_quartz'))
                cv.set(x, -1, z, 'gray_concrete' if not edge else 'light_gray_concrete')
                if 37.5 <= r < 38.5 and (int(math.degrees(math.atan2(z, x)) + 360)) % 15 == 0: cv.set(x, 0, z, 'sea_lantern')
    for k in range(4):                                                  # spokes
        for d in range(16, 36):
            for w in (-1, 0, 1):
                x, z = rot_xz(d, w, k)
                cv.set(x, 0, z, 'smooth_quartz' if w == 0 else ('iron_block' if d % 4 == 0 else 'light_gray_concrete'), force=False); cv.set(x, -1, z, 'gray_concrete', force=False)
            if d % 6 == 0:
                x, z = rot_xz(d, 0, k); cv.set(x, -2, z, 'end_rod[facing=down]')
    for k in range(4):                                                  # pods on the diagonals
        x0, z0 = rot_xz(27, 27, k)
        disc(cv, x0, 0, z0, 5.5, 'smooth_quartz'); disc(cv, x0, -1, z0, 5.5, 'gray_concrete'); disc(cv, x0, -2, z0, 3.5, 'light_gray_concrete')
        for y in range(1, 5): disc(cv, x0, y, z0, 5.5, lambda x, yy, z: 'light_blue_stained_glass' if yy in (2, 3) and (x + z) % 3 else 'white_concrete', r_in=4.5)
        disc(cv, x0, 5, z0, 5.5, 'white_concrete', r_in=3); disc(cv, x0, 6, z0, 3.5, 'light_gray_concrete'); cv.set(x0, 7, z0, 'lightning_rod[facing=up]')
        # doorways where the ring passes through
        ux, uz = (z0 / 38.2, -x0 / 38.2)
        for sgn in (-1, 1):
            for t in (4, 5, 6):
                for w in (-1, 0, 1):
                    px = x0 + round(sgn * t * ux + w * x0 / 38.2); pz = z0 + round(sgn * t * uz + w * z0 / 38.2)
                    for y in (1, 2, 3): cv.set(px, y, pz, None)
        for (dx, dz, s) in ((0, 0, 'lectern[facing=south]'), (1, 0, 'observer[facing=up]'), (-1, 0, 'observer[facing=up]')):
            ox, oz = round(x0 + 2.6 * x0 / 38.2) + dx, round(z0 + 2.6 * z0 / 38.2) + dz
            if cv.empty(ox, 1, oz): cv.set(ox, 1, oz, s)
        cv.set(round(x0 - 3 * x0 / 38.2), 1, round(z0 - 3 * z0 / 38.2), 'quartz_stairs[facing=%s,half=bottom]' % ('east' if x0 < 0 else 'west'))
        cv.set(x0, 4, z0, 'sea_lantern')
    return cv

def planet(i):
    cv = Canvas(93 + i); nz = cv.noise
    if i == 0: m = lambda x, y, z: ('snow_block' if abs(y + 4) > 5.5 else ('moss_block' if nz.n3(x + 9, y, z + 9, 4.0) > 0.56 else 'light_blue_concrete'))
    elif i == 1: m = lambda x, y, z: ('red_sandstone' if nz.n3(x, y, z, 4.0) > 0.5 else 'orange_terracotta') if (y // 2) % 3 else 'terracotta'
    elif i == 2: m = lambda x, y, z: 'blue_ice' if nz.n3(x, y, z, 3.5) > 0.6 else ('packed_ice' if nz.n3(x, y, z, 3.5) > 0.42 else 'snow_block')
    else: m = lambda x, y, z: 'amethyst_block' if nz.n3(x, y, z, 3.5) > 0.6 else ('purpur_block' if (y // 2) % 2 else 'purple_terracotta')
    sphere(cv, 0, -4, 0, 7.5, m, ymax=0)
    gen_pad(cv, 0, 0, 0, 'diamond', frame='smooth_stone'); gem_marker(cv, 0, 0, 0, 'diamond')
    sphere(cv, 9, 3, -6, 1.8, ('calcite', 'tuff', 'white_concrete', 'obsidian')[i])
    return cv

def asteroid(i, r=None):
    cv = Canvas(100 + i)
    r = r or cv.rng.uniform(1.6, 3.2)
    boulder(cv, 0, 0, 0, r, [('cobbled_deepslate', 4), ('tuff', 3), ('andesite', 2), ('deepslate_iron_ore', 0.4), ('deepslate_gold_ore', 0.2), ('raw_iron_block', 0.1)], seed=i * 7, squash=0.9)
    return cv

def comet(i):
    """head at the origin, tail along local (+x, +z)"""
    cv = Canvas(130 + i)
    curve(cv, [(0, 0, 0), (7, 1, 6), (13, 3, 14), (22, 6, 22)], [('light_blue_stained_glass', 3), ('white_stained_glass', 2)], taper=(3.0, 0.4))
    curve(cv, [(2, 1, -1), (9, 3, 3), (18, 6, 10)], 'white_stained_glass', taper=(1.6, 0.4))
    sphere(cv, 0, 0, 0, 3.6, [('packed_ice', 3), ('blue_ice', 2), ('snow_block', 1)])
    return cv

def build():
    mb = MapBuilder(909)
    mb.put(sun(), 0, 0, kind='mid'); mb.put(station(), 0, 0, kind='mid')
    mb.bases(planet_base, 118, 22)
    rng = mb.cv.rng
    for k in range(4):
        x, z = rot_xz(57, 57, k); mb.put(planet(k), x, z, kind='diamond')
        x, z = rot_xz(43, 43, k); mb.put(asteroid(50 + k, 4.6), x, z, y=-2, kind='extra')
        x, z = rot_xz(92, 92, k); mb.put(comet(k), x, z, y=4, k=k, kind='extra')
    for i in range(26):                                                 # asteroid belt
        a = rng.uniform(0, 360); r = rng.uniform(50, 66)
        d = (a % 90) - 45
        if abs(d) < 16 or abs(abs(d) - 45) < 4: continue
        mb.put(asteroid(i), round(r * math.cos(math.radians(a))), round(r * math.sin(math.radians(a))), y=rng.randint(-6, 6), kind='rock')
    for a in range(0, 360, 4):                                          # the dotted orbit of the small planets
        d = (a % 90) - 45
        if abs(d) < 9: continue
        x, z = round(80.6 * math.cos(math.radians(a))), round(80.6 * math.sin(math.radians(a)))
        mb.cv.set(x, 0, z, 'sea_lantern' if a % 12 == 0 else 'white_stained_glass')
    return mb

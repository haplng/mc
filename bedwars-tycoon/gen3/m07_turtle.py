"""Map 7 - 거북: sea turtles carrying the bases swim towards a sand atoll with a lagoon; baby turtles carry the diamonds."""
import math
from canvas import Canvas
from kit import *

ID = 'turtle'; NAME = '거북'
GATE = dict(frame='dark_prismarine', roof_full='lime_terracotta', plaza='sand', glass='light_blue_stained_glass')
SAND = dict(top='sand', sub=[('sandstone', 3), ('smooth_sandstone', 1)], sub_n=4, under=[('sandstone', 3), ('stone', 3), ('andesite', 2), ('calcite', 1)],
            tip=[('stone', 2), ('cobbled_deepslate', 1), ('andesite', 1)], strata=['sandstone', 'sandstone', 'stone', 'calcite', 'stone', 'andesite'])

def paddle(cv, cx, cy, cz, rx, rz, ang, mat, droop=2):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang)); R = int(max(rx, rz)) + 2
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            u = dx * ca + dz * sa; v = -dx * sa + dz * ca
            if (u / rx) ** 2 + (v / rz) ** 2 < 1:
                y = cy - int(max(0.0, u) / rx * droop + 0.3)
                put(cv, cx + dx, y, cz + dz, mat); put(cv, cx + dx, y - 1, cz + dz, mat)

def turtle(cv, rx, rz, depth, f, dye=None):
    """body of a turtle whose flat back is the floor at y=0; f scales head and flippers"""
    SK = [('lime_terracotta', 4), ('green_terracotta', 1)]; BELLY = [('yellow_terracotta', 3), ('smooth_sandstone', 1)]
    def scute(x, y, z):
        c = (x + 300) // 5; zz = z + (2 if c % 2 else 0)
        if (x + 300) % 5 == 0 or (zz + 300) % 5 == 0: return 'brown_terracotta'
        return 'green_terracotta' if (c + (zz + 300) // 5) % 3 else 'lime_terracotta'
    for y in range(-depth, 1):
        s = math.sqrt(max(0.0, 1 - (y / (depth + 0.5)) ** 2))
        for x in range(-int(rx) - 1, int(rx) + 2):
            for z in range(-int(rz) - 1, int(rz) + 2):
                d = math.hypot(x / (rx * s + 0.5), z / (rz * s + 0.5)) if s > 0.05 else 9
                if d < 1:
                    if y == 0: m = (dye + '_concrete') if (dye and math.hypot(x / (rx + 0.5), z / (rz + 0.5)) > 0.9) else scute(x, y, z)
                    elif y >= -2: m = 'dark_prismarine' if d > 0.86 else 'green_terracotta'
                    else: m = cv.pick(BELLY)
                    cv.set(x, y, z, m)
    # head, neck, tail, flippers
    hz = rz + 4.5 * f
    ellipsoid(cv, 0, -2, round(hz), 3.6 * f, 3.0 * f, 5.2 * f, SK, ymax=0)
    ellipsoid(cv, 0, -2, round(rz), 2.6 * f, 2.2 * f, 3 * f, SK, ymax=-1)
    ez = round(hz + 2.5 * f); ex = round(3.4 * f)
    for sx in (-1, 1):
        cv.set(sx * ex, -1, ez, 'black_concrete'); cv.set(sx * ex, -1, ez - 1, 'white_concrete')
        paddle(cv, sx * round(rx + 4 * f), -2, round(rz * 0.45), 6.5 * f, 3.4 * f, 25 if sx > 0 else 155, SK)
        paddle(cv, sx * round(rx * 0.75 + 2), -2, -round(rz * 0.85), 4.2 * f, 2.4 * f, -40 if sx > 0 else 220, SK, droop=1)
    cone_z = round(rz)
    for i in range(round(4 * f)):
        w = max(0, round((4 * f - i) / 2) - 1)
        for x in range(-w, w + 1): cv.set(x, -2, -cone_z - i, 'lime_terracotta'); cv.set(x, -3, -cone_z - i, 'lime_terracotta')

def turtle_base(dye):
    cv = Canvas(sum(map(ord, dye)) + 7)
    turtle(cv, 12, 14, 7, 1.0, dye)
    disc(cv, 0, 0, -5, 7.5, [('grass_block', 5), ('moss_block', 1)])
    # beach hut
    Wl = 'bamboo_planks'
    box(cv, -4, 1, -10, 4, 3, -3, Wl, hollow=True); box(cv, -3, 1, -9, 3, 3, -4, None)
    for x in (-4, 4):
        for z in (-10, -3):
            for y in range(1, 4): cv.set(x, y, z, 'stripped_jungle_log[axis=y]')
    box(cv, -5, 4, -11, 5, 4, -2, 'hay_block[axis=x]'); box(cv, -4, 5, -10, 4, 5, -3, 'hay_block[axis=x]'); box(cv, -2, 6, -9, 2, 6, -4, dye + '_wool')
    box(cv, -5, 4, -11, 5, 4, -11, dye + '_wool'); box(cv, -5, 4, -2, 5, 4, -2, dye + '_wool')
    for x in (-1, 0, 1):
        for y in (1, 2, 3): cv.set(x, y, -3, None)
    for z in (-7, -6):
        cv.set(-4, 2, z, 'bamboo_fence[north=true,south=true]'); cv.set(4, 2, z, 'bamboo_fence[north=true,south=true]')
    box(cv, -3, 0, -9, 3, 0, -4, 'bamboo_mosaic')
    gen_pad(cv, 0, 0, -7, 'iron', frame='bamboo_mosaic')
    cv.set(-3, 1, -9, 'chest[facing=east]'); cv.set(3, 1, -9, 'ender_chest[facing=west]'); hang_lamp(cv, -2, 3, -5); hang_lamp(cv, 2, 3, -5)
    cv.set(-3, 1, -4, 'barrel[facing=up]'); cv.set(3, 1, -4, 'composter'); cv.set(-3, 1, -6, dye + '_carpet'); cv.set(3, 1, -6, dye + '_carpet')
    palm(cv, 8, 1, -1, 7, lean=(1, 0)); palm(cv, -8, 1, -6, 5, lean=(-1, 0))
    for (x, z, s) in ((6, -8, 'fern'), (-6, -2, 'short_grass'), (7, -4, 'short_grass'), (-7, -8, 'fern'), (5, -1, 'poppy'), (-6, -10, 'short_grass')):
        if cv.name(x, 0, z) in ('grass_block', 'moss_block') and cv.empty(x, 1, z): cv.set(x, 1, z, s)
    stall(cv, -7, 1, 5, 3, 'white', dye, post='bamboo_fence'); stall(cv, 7, 1, 5, 1, 'white', dye, post='bamboo_fence')
    bed(cv, dye, 0, 1, 9)
    team_markers(cv, dye, spawn=(0, 1, -4), bedpos=(0, 1, 9), gen=(0, 0, -7), shop=(-7, 1, 5), upg=(7, 1, 5))
    return cv

def baby(i):
    cv = Canvas(77 + i)
    turtle(cv, 7, 8.5, 5, 0.62)
    gen_pad(cv, 0, 0, 0, 'diamond', frame='dark_prismarine'); gem_marker(cv, 0, 0, 0, 'diamond')
    cv.set(-4, 1, -4, 'sandstone_wall'); cv.set(-4, 2, -4, 'lantern[hanging=false]'); cv.set(4, 1, -4, 'turtle_egg[eggs=3,hatch=0]')
    return cv

def atoll():
    cv = Canvas(71)
    hm = island(cv, 0, 0, 0, (37, 37), 17, SAND, seed=3, flat=0.78, hill=1.6, rough=0.16)
    nz = cv.noise
    # lagoon: two blocks deep in the middle, one near the shore, a small islet left standing in the centre
    floor = [('sand', 5), ('gravel', 2), ('clay', 1)]
    for x in range(-22, 23):
        for z in range(-22, 23):
            r = math.hypot(x, z) + (nz.f2(x + 50, z + 50, 7.0) - 0.5) * 5
            if r < 5.5 or r >= 19: continue
            deep = r < 15 and r > 7.5
            cv.set(x, 0, z, 'water')
            if deep:
                cv.set(x, -1, z, 'water'); cv.set(x, -2, z, cv.pick(floor))
                q = cv.rng.random()
                if q < 0.05: cv.set(x, -2, z, cv.rng.choice(('tube_coral_block', 'brain_coral_block', 'bubble_coral_block', 'fire_coral_block', 'horn_coral_block')))
                elif q < 0.08: cv.set(x, -2, z, 'sea_lantern')
                elif q < 0.13: cv.set(x, -1, z, 'sea_pickle[pickles=%d,waterlogged=true]' % cv.rng.randint(1, 4))
            else: cv.set(x, -1, z, cv.pick(floor))
    # centre islet with a big palm and a chest of treasure
    disc(cv, 0, 1, 0, 3, 'sand'); palm(cv, 0, 2, 0, 9, lean=(1, 0)); cv.set(-2, 2, 1, 'chest[facing=south]'); cv.set(-1, 2, -2, 'gold_block'); cv.set(2, 2, 2, 'raw_gold_block')
    # four flush piers over the lagoon
    for k in range(4):
        for d in range(4, 22):
            for w in (-1, 0, 1):
                x, z = rot_xz(d, w, k)
                if cv.name(x, 0, z) == 'water' or d < 7 or d > 18:
                    if cv.name(x, 0, z) in ('water', 'sand'): cv.set(x, 0, z, 'spruce_planks' if w == 0 else 'stripped_spruce_wood')
            if d % 4 == 0:
                for w in (-1, 1):
                    x, z = rot_xz(d, w, k)
                    if cv.name(x, -1, z) == 'water': cv.set(x, -1, z, 'spruce_fence[waterlogged=true]')
        x, z = rot_xz(28, 0, k); gen_pad(cv, x, 0, z, 'emerald', frame='smooth_sandstone'); gem_marker(cv, x, 0, z, 'emerald')
    # palms, huts, umbrellas on the ring
    for a in range(20, 360, 45):
        r = 27 + cv.rng.randint(-2, 3); x, z = round(r * math.cos(math.radians(a))), round(r * math.sin(math.radians(a)))
        y = hm.get((x, z))
        if y is not None and cv.name(x, y, z) == 'sand': palm(cv, x, y + 1, z, cv.rng.randint(6, 9), lean=(1 if x > 0 else -1, 0))
    for k in range(4):                                                  # stilt huts on the diagonals
        x, z = rot_xz(21, 21, k)
        for sx in (-2, 2):
            for sz in (-2, 2):
                for y in range(1, 4): cv.set(x + sx, y, z + sz, 'stripped_jungle_log[axis=y]')
        box(cv, x - 3, 4, z - 3, x + 3, 4, z + 3, 'bamboo_planks'); box(cv, x - 3, 5, z - 3, x + 3, 7, z + 3, 'bamboo_mosaic', hollow=True); box(cv, x - 2, 5, z - 2, x + 2, 7, z + 2, None)
        box(cv, x - 4, 8, z - 4, x + 4, 8, z + 4, 'hay_block[axis=x]'); box(cv, x - 2, 9, z - 2, x + 2, 9, z + 2, 'hay_block[axis=z]'); cv.set(x, 10, z, 'hay_block[axis=y]')
        dx, dz = (-1 if x > 0 else 1), (-1 if z > 0 else 1)
        for y in (5, 6): cv.set(x + 3 * dx, y, z, None)
        cv.set(x - 3 * dx, 6, z, 'bamboo_fence[north=true,south=true]'); cv.set(x, 6, z - 3 * dz, 'bamboo_fence[east=true,west=true]')
        for i in range(4):                                              # stairs up from the sand
            cv.set(x + (4 + i) * dx, 4 - i, z, 'bamboo_stairs[facing=%s,half=bottom]' % ('east' if dx < 0 else 'west'))
            for yy in range(1, 4 - i): cv.set(x + (4 + i) * dx, yy, z, 'bamboo_planks')
        cv.set(x - 2 * dx, 5, z - 2 * dz, 'barrel[facing=up]'); cv.set(x - 2 * dx, 5, z + 2 * dz, 'white_bed[facing=%s,part=foot]' % ('south' if dz > 0 else 'north')) if False else None
        cv.set(x - 2 * dx, 5, z + 2 * dz, 'crafting_table'); cv.set(x, 7, z, 'lantern[hanging=true]'); cv.set(x - 2 * dx, 5, z, 'lime_carpet'); cv.set(x - 1 * dx, 5, z, 'lime_carpet')
    for i, a in enumerate(range(0, 360, 90)):                           # beach umbrellas
        x, z = round(31 * math.cos(math.radians(a + 28))), round(31 * math.sin(math.radians(a + 28)))
        y = hm.get((x, z))
        if y is None or cv.name(x, y, z) != 'sand': continue
        for yy in range(1, 4): cv.set(x, y + yy, z, 'birch_fence')
        col = ('orange', 'magenta', 'light_blue', 'purple')[i]
        disc(cv, x, y + 4, z, 2.2, sectors(x, z, 8, [col + '_wool', 'white_wool'])); cv.set(x, y + 5, z, col + '_wool')
    return cv

def jelly(i):
    cv = Canvas(79 + i)
    col = ('magenta', 'light_blue', 'pink', 'purple')[i % 4] + '_stained_glass'
    sphere(cv, 0, 0, 0, 4.2, col, hollow=True, ymin=0); disc(cv, 0, 0, 0, 3, 'white_stained_glass')
    cv.set(0, 1, 0, 'sea_lantern'); cv.set(0, 2, 0, 'sea_lantern')
    for a in range(0, 360, 60):
        x, z = 3 * math.cos(math.radians(a)), 3 * math.sin(math.radians(a))
        pts = [(x, -1, z), (x * 1.3, -4, z * 1.3 + 1), (x * 0.9, -7, z * 0.9 - 1), (x * 1.2 + 1, -10 - (a % 120) // 30, z * 1.2)]
        curve(cv, pts, col)
    return cv

def build():
    mb = MapBuilder(707)
    mb.put(atoll(), 0, 0, kind='mid')
    mb.bases(turtle_base, 106, 21)
    for k in range(4):
        x, z = rot_xz(45, 45, k); mb.put(baby(k), x, z, k=(k + 1) % 4, kind='diamond')
        x, z = rot_xz(66, 0, k); mb.put(jelly(k), x, z, y=9, kind='extra')
    return mb

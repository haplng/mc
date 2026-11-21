"""Map 3 - 서커스: big-top tents round one huge X-shaped fairground (carousel in the middle, rides on the four arms)."""
import math
from canvas import Canvas
from kit import *

ID = 'circus'; NAME = '서커스'
GATE = dict(frame='red_wool', roof_full='yellow_wool', plaza='birch_planks', glass='yellow_stained_glass')

def mini_tent(cv, cx, y, cz, r, a, b, door=(0, 1), n=12):
    st = sectors(cx, cz, n, [a + '_wool', b + '_wool'])
    for yy in range(y, y + 3): disc(cv, cx, yy, cz, r, st, r_in=r - 1)
    h = int(r) + 2
    for i in range(h):
        rr = (r + 1) * (1 - i / h)
        disc(cv, cx, y + 3 + i, cz, rr, st, r_in=(rr - 1.3 if rr > 1.5 else None))
    cv.set(cx, y + 3 + h, cz, 'gold_block')
    for w in (-1, 0, 1):
        for d in range(int(r) - 1, int(r) + 2):
            x, z = cx + door[0] * d + door[1] * w, cz + door[1] * d + door[0] * w
            for yy in (y, y + 1): cv.set(x, yy, z, None)

def tent_base(dye):
    cv = Canvas(sum(map(ord, dye)) + 3)
    T = dye + '_wool'; W = 'white_wool'; TC = dye + '_concrete'
    if dye == 'white': W = 'light_gray_wool'
    disc(cv, 0, 0, 0, 13, lambda x, y, z: TC if math.hypot(x, z) >= 11.5 else 'birch_planks')
    st = sectors(0, 0, 24, [T, W])
    for y in (-1, -2, -3): disc(cv, 0, y, 0, 13, st, r_in=12); disc(cv, 0, y, 0, 12, 'dark_oak_planks')
    under_dome(cv, 0, -3, 0, 12, 6, ['dark_oak_planks', 'spruce_planks', 'spruce_planks'])
    cv.set(0, -10, 0, 'lantern[hanging=true]')
    # the big top
    cx, cz = 0, -3
    ts = sectors(cx, cz, 16, [T, W])
    for y in range(1, 5): disc(cv, cx, y, cz, 9, ts, r_in=8)
    for i in range(10):
        r = 10 - i
        disc(cv, cx, 5 + i, cz, r, ts, r_in=(r - 1.3 if r > 1.5 else None))
    disc(cv, cx, 0, cz, 5.5, TC, r_in=4.5)                                  # the ring kerb, flush with the floor
    flag(cv, cx, 15, cz, 5, dye, d=(1, 0), pole='spruce_fence')
    for x in (-1, 0, 1):
        for y in (1, 2, 3):
            for z in (5, 6): cv.set(x, y, z, None)
    for x in (-2, 2):
        for y in (1, 2, 3, 4): cv.set(x, y, 6, 'gold_block' if y == 4 else TC)
    for a in range(200, 341, 14):                                           # benches along the back wall
        dx, dz = 7 * math.cos(math.radians(a)), 7 * math.sin(math.radians(a))
        x, z = cx + round(dx), cz + round(dz)
        if cv.empty(x, 1, z): cv.set(x, 1, z, stair('spruce', towards(dx, dz)))
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = cx + sx * 4, cz + sz * 4
            for y in range(1, 6): cv.set(x, y, z, 'spruce_fence')
            cv.set(x, 6, z, 'lantern[hanging=false]')
    gen_pad(cv, cx, 0, cz, 'iron', frame='smooth_sandstone')
    cv.set(-7, 1, 0, 'chest[facing=east]'); cv.set(7, 1, 0, 'ender_chest[facing=west]')
    # the shopkeepers sit in ticket booths against the tent wall
    for sx in (-1, 1):
        for z in (-4, -2):
            for y in (1, 2, 3): cv.set(sx * 8, y, z, TC)
        for z in (-4, -3, -2):                                             # striped awning, high enough to leave the name readable
            cv.set(sx * 8, 4, z, T if z == -3 else W); cv.set(sx * 7, 4, z, W if z == -3 else T)
        cv.set(sx * 7, 1, -3, TC)                                           # counter
    # outside: balloons, a few bales and barrels where the stalls used to be
    for (x, z, s) in ((-10, 4, 'hay_block[axis=y]'), (-10, 5, 'barrel[facing=up]'), (-9, 5, 'hay_block[axis=x]'), (10, 4, 'barrel[facing=up]'), (10, 5, 'hay_block[axis=y]'), (9, 5, 'barrel[facing=up]')):
        cv.set(x, 1, z, s)
    cv.set(-10, 2, 5, 'hay_block[axis=y]'); cv.set(10, 2, 5, 'lantern[hanging=false]')
    for i, (x, z, col) in enumerate(((11, 1, 'orange'), (-11, 0, 'magenta'), (10, -1, 'light_blue'))):
        for y in range(1, 4 + i % 2): cv.set(x, y, z, 'oak_fence')
        cv.set(x, 4 + i % 2, z, col + '_wool'); cv.set(x, 5 + i % 2, z, col + '_wool')
    bed(cv, dye, 0, 1, 9)
    team_markers(cv, dye, spawn=(0, 1, 2), bedpos=(0, 1, 9), gen=(cx, 0, cz), shop=(-8, 1, -3), upg=(8, 1, -3))
    return cv

def ferris(cv, x, y, z, R=7):
    hy = y + R + 2
    for sx in (-2, 2):                                                       # A-frames
        line(cv, (x + sx, y, z - 4), (x + sx // 2, hy, z), 'iron_block'); line(cv, (x + sx, y, z + 4), (x + sx // 2, hy, z), 'iron_block')
    vdisc(cv, x, hy, z, R, 'white_concrete', axis='x', r_in=R - 1)
    cols = ('orange', 'magenta', 'light_blue', 'purple', 'yellow', 'lime', 'pink', 'cyan')
    for i, a in enumerate(range(0, 360, 45)):
        dz, dy = R * math.cos(math.radians(a)), R * math.sin(math.radians(a))
        line(cv, (x, hy, z), (x, hy + round(dy * 0.85), z + round(dz * 0.85)), 'light_gray_concrete')
        for w in (-1, 0, 1): cv.set(x + w, hy + round(dy) - 1, z + round(dz), cols[i] + '_wool')
        cv.set(x, hy + round(dy), z + round(dz), 'white_concrete')
    for w in (-1, 0, 1): cv.set(x + w, hy, z, 'gold_block')

def lobe(kind):
    """one arm end of the fairground; local (+x, +z) points outwards along the diagonal"""
    cv = Canvas(60 + kind)
    cols = [('purple', 'yellow'), ('orange', 'light_blue')][kind % 2]
    disc(cv, 0, 0, 0, 10, lambda x, y, z: (cols[0] + '_concrete') if math.hypot(x, z) >= 8.5 else 'birch_planks')
    st = sectors(0, 0, 20, [cols[0] + '_wool', cols[1] + '_wool'])
    for y in (-1, -2): disc(cv, 0, y, 0, 10, st, r_in=9); disc(cv, 0, y, 0, 9, 'dark_oak_planks')
    under_dome(cv, 0, -2, 0, 9, 5, ['dark_oak_planks', 'spruce_planks'])
    gen_pad(cv, -2, 0, -2, 'diamond', frame='smooth_quartz'); gem_marker(cv, -2, 0, -2, 'diamond')
    if kind % 2 == 0: ferris(cv, 4, 1, 3, 6)
    else:
        mini_tent(cv, 4, 1, 4, 4, cols[0], cols[1], door=(-1, 0))
        cv.set(5, 1, 5, 'barrel[facing=up]'); cv.set(5, 1, 3, 'barrel[facing=up]'); cv.set(6, 1, 4, 'crafting_table'); cv.set(4, 3, 4, 'lantern[hanging=true]') if False else None
        cv.set(4, 1, 6, 'hay_block[axis=y]'); cv.set(2, 1, -6, 'target'); cv.set(2, 2, -6, 'target')
    for (x, z) in ((-7, 4), (4, -7)): post_lamp(cv, x, 1, z, 'spruce_fence', 'lantern', 3)
    return cv

def fairground(L=40):
    cv = Canvas(33)
    P = 'birch_planks'
    st = sectors(0, 0, 32, ['purple_wool', 'yellow_wool'])
    # catwalks along the diagonals (drawn first, the plaza goes over them)
    for sx in (-1, 1):
        for sz in (-1, 1):
            for i in range(10, L - 6):
                for w in range(-3, 4):
                    x, z = sx * i + (w if sx * sz > 0 else w), sz * i - (w if sx * sz > 0 else -w)
                    for e in (0, 1):
                        if abs(w) == 3 and e: continue
                        cv.set(x + e, 0, z, 'spruce_planks' if abs(w) == 3 else (P if (i // 2) % 2 else 'stripped_birch_wood'), force=(abs(w) != 3))
                        cv.set(x + e, -1, z, 'dark_oak_planks')
                if i % 7 == 3 and i > 18:
                    for w in (-3, 3):
                        x, z = sx * i + w, sz * i - (w if sx * sz > 0 else -w)
                        post_lamp(cv, x, 1, z, 'spruce_fence', 'lantern', 3)
    disc(cv, 0, 0, 0, 17, lambda x, y, z: 'purple_concrete' if math.hypot(x, z) >= 15.5 else P)
    for y in (-1, -2, -3): disc(cv, 0, y, 0, 17, st, r_in=16); disc(cv, 0, y, 0, 16, 'dark_oak_planks')
    under_dome(cv, 0, -3, 0, 16, 9, ['dark_oak_planks', 'spruce_planks', 'spruce_planks'])
    cv.set(0, -13, 0, 'lantern[hanging=true]')
    # carousel
    disc(cv, 0, 1, 0, 10, lambda x, y, z: 'smooth_quartz' if math.hypot(x, z) >= 8.5 else 'red_concrete' if (int(math.degrees(math.atan2(z, x)) + 360) // 30) % 2 else 'white_concrete')
    cyl(cv, 0, 2, 12, 0, 1.5, lambda x, y, z: 'gold_block' if y in (4, 8, 12) else 'quartz_pillar[axis=y]')
    cs = sectors(0, 0, 16, ['purple_wool', 'yellow_wool'])
    disc(cv, 0, 9, 0, 11, cs, r_in=9.5)
    for i in range(7):
        r = 11 - i * 1.6
        disc(cv, 0, 10 + i, 0, r, cs, r_in=(r - 1.8 if r > 2 else None))
    cv.set(0, 17, 0, 'gold_block'); cv.set(0, 18, 0, 'end_rod[facing=up]')
    horse = ('white_concrete', 'brown_concrete', 'light_gray_concrete', 'black_concrete')
    for i, a in enumerate(range(0, 360, 45)):
        x, z = round(9 * math.cos(math.radians(a))), round(9 * math.sin(math.radians(a)))
        for y in range(2, 9): cv.set(x, y, z, 'birch_fence')
        x, z = round(6 * math.cos(math.radians(a + 22))), round(6 * math.sin(math.radians(a + 22)))
        for y in range(2, 9): cv.set(x, y, z, 'birch_fence')
        cv.set(x, 3 + i % 2, z, horse[i % 4])
        dx, dz = -math.sin(math.radians(a + 22)), math.cos(math.radians(a + 22))
        cv.set(x + round(dx), 3 + i % 2, z + round(dz), horse[i % 4]); cv.set(x + round(dx), 4 + i % 2, z + round(dz), stair('quartz', towards(-dx, -dz)))
    for k in range(4):
        x, z = rot_xz(14, 0, k); gen_pad(cv, x, 0, z, 'emerald', frame='smooth_quartz'); gem_marker(cv, x, 0, z, 'emerald')
    return cv

def balloons(i):
    cv = Canvas(70 + i)
    box(cv, -1, -1, -1, 1, 0, 1, 'spruce_planks'); box(cv, -1, 1, -1, 1, 1, 1, 'spruce_fence'); cv.set(0, 1, 0, 'barrel[facing=up]')
    cols = ['orange', 'magenta', 'light_blue', 'purple', 'lime', 'yellow', 'pink']
    cv.rng.shuffle(cols)
    spots = ((0, 13, 0, 2.6), (-4, 10, 2, 2.2), (4, 11, -2, 2.2), (2, 9, 4, 1.8), (-3, 8, -4, 1.8))
    for (x, y, z, r), col in zip(spots, cols):
        line(cv, (0, 2, 0), (x, y - int(r), z), 'white_stained_glass')
        sphere(cv, x, y, z, r, col + '_concrete')
    return cv

def build():
    mb = MapBuilder(303)
    L = 35
    mb.put(fairground(L), 0, 0, kind='mid')
    for k in range(4):
        x, z = rot_xz(L, L, k); mb.put(lobe(k), x, z, k=k, kind='mid')
    mb.bases(tent_base, 81.5, 23)
    for k in range(4):
        x, z = rot_xz(37, 0, k); mb.put(balloons(k), x, z, y=-2, kind='extra')
    return mb

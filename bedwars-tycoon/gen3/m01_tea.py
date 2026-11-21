"""Map 1 - 티타임: teacups on saucers in an even ring round a tiered cake; macarons carry the diamonds."""
import math
from canvas import Canvas
from kit import *

ID = 'tea'; NAME = '티타임'
GATE = dict(frame='smooth_quartz', roof_full='pink_concrete', plaza='white_concrete', glass='pink_stained_glass')

def cup_base(dye):
    cv = Canvas(sum(map(ord, dye)) + 1)
    T = dye + '_concrete'; W = 'white_concrete'
    # saucer: a shallow dish with a team ring
    def top(x, y, z):
        r = math.hypot(x, z)
        return T if 9.5 <= r < 11.5 else ('smooth_quartz' if r >= 12.5 else W)
    disc(cv, 0, 0, 0, 13, top); disc(cv, 0, -1, 0, 11, W); disc(cv, 0, -2, 0, 8, 'smooth_quartz'); disc(cv, 0, -3, 0, 5, W, r_in=2)
    # cup (a round room; the tea is its glass ceiling)
    cx, cz = 0, -3
    prof = {1: 5.5, 2: 6.5, 3: 7.3, 4: 8, 5: 8, 6: 8, 7: 8, 8: 8.4}
    for y, r in prof.items():
        mat = W if y in (4, 5) else ('smooth_quartz' if y == 8 else T)
        disc(cv, cx, y, cz, r, mat, r_in=r - 1)
    for a in range(0, 360, 30):                                   # little dots under the band
        x, z = cx + round(8 * math.cos(math.radians(a))), cz + round(8 * math.sin(math.radians(a)))
        if cv.get(x, 6, z): cv.set(x, 6, z, 'gold_block')
    disc(cv, cx, 7, cz, 7, 'orange_stained_glass')                # tea
    disc(cv, cx + 2, 8, cz - 2, 2, 'yellow_concrete'); disc(cv, cx + 2, 8, cz - 2, 1, 'white_concrete'); cv.set(cx + 2, 8, cz - 2, 'yellow_concrete')
    for i, (x, y, z) in enumerate(((-2, 10, -1), (-2, 11, -2), (-3, 12, -2), (-3, 13, -3), (-2, 14, -4), (-2, 15, -4), (1, 11, -5), (1, 12, -6), (0, 13, -6))):
        cv.set(cx + x, y, cz + z + 3, 'white_stained_glass')      # steam
    for x in (-1, 0, 1):                                          # door
        for y in (1, 2, 3):
            for z in (2, 3, 4, 5): cv.set(x, y, z, None)
    for x in (-2, 2):
        for y in (1, 2, 3): cv.set(x, y, 4, 'smooth_quartz', force=False)
    for y in (3, 6):                                              # handle
        for x in (-9, -10, -11):
            for z in (-4, -3): cv.set(x, y, z, T)
    for y in (4, 5):
        for z in (-4, -3): cv.set(-12, y, z, T)
    # tea-bag tag hanging over the rim
    for a in (38, 44, 50):
        x, z = cx + round(9 * math.sin(math.radians(a))), cz + round(9 * math.cos(math.radians(a)))
        for y in (3, 4, 5): cv.set(x, y, z, 'white_wool' if y == 4 else 'light_gray_wool')
    x, z = cx + round(9 * math.sin(math.radians(44))), cz + round(9 * math.cos(math.radians(44)))
    for y in (6, 7, 8, 9): cv.set(x, y, z, 'white_wool')
    cv.set(cx + round(8 * math.sin(math.radians(44))), 9, cz + round(8 * math.cos(math.radians(44))), 'white_wool')
    # inside
    gen_pad(cv, 0, 0, -5, 'iron', frame=W)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2 and cv.empty(dx, 1, -5 + dz): cv.set(dx, 1, -5 + dz, dye + '_carpet')
    cv.set(-5, 1, -6, T); cv.set(5, 1, -6, T)                       # team-coloured stands (the user's fix in the red base)
    cv.set(-5, 2, -6, 'chest[facing=east]'); cv.set(5, 2, -6, 'ender_chest[facing=west]')
    hang_lamp(cv, -3, 6, -2); hang_lamp(cv, 3, 6, -2); hang_lamp(cv, 0, 6, -8)
    table(cv, -5, 1, -1, 'birch', chairs=((0, 1),)); cv.set(5, 1, -1, 'barrel[facing=up]'); cv.set(5, 2, -1, 'flower_pot')
    cv.set(4, 1, 0, 'quartz_block'); cv.set(-4, 1, -9, 'quartz_block'); cv.set(4, 1, -9, 'quartz_block'); cv.set(4, 2, -9, 'white_candle[candles=3,lit=true]')
    # on the saucer
    for x, y, z in ((-9, 1, 2), (-8, 1, 2), (-9, 1, 3), (-8, 1, 3), (-9, 2, 2), (-10, 1, 0)): cv.set(x, y, z, 'quartz_block')      # sugar cubes
    for x, y, z in ((8, 1, 2), (9, 1, 2), (8, 1, 3)): cv.set(x, y, z, 'yellow_concrete')                                           # lemon wedge
    cv.set(9, 1, 3, 'white_concrete'); cv.set(8, 2, 2, 'yellow_concrete')
    disc(cv, 8, 1, -8, 2.6, lambda x, y, z: 'dark_oak_planks' if (x * 7 + z * 13) % 5 == 0 else 'stripped_oak_wood')              # biscuit
    # the two shopkeepers stand inside the cup wall, under its flare; the ring block in front of each is the counter
    # (the user opened this niche by hand in the red base)
    for sx in (-1, 1):
        cv.set(sx * 6, 2, -3, None)                                       # the window they look out of
        cv.set(sx * 7, 1, -3, T); cv.set(sx * 7, 2, -3, dye + '_stained_glass')
        cv.set(sx * 6, 1, -4, T); cv.set(sx * 6, 1, -2, T)
    bed(cv, dye, 0, 1, 9)
    team_markers(cv, dye, spawn=(0, 1, -1), bedpos=(0, 1, 9), gen=(0, 0, -5), shop=(-6, 1, -3), upg=(6, 1, -3))
    return cv

def cake():
    cv = Canvas(11)
    SP = 'smooth_sandstone'; CR = 'white_concrete'; PK = 'pink_concrete'
    disc(cv, 0, 0, 0, 17, lambda x, y, z: 'smooth_quartz' if math.hypot(x, z) >= 15.5 else CR)
    disc(cv, 0, -1, 0, 14, 'smooth_quartz'); disc(cv, 0, -2, 0, 9, 'quartz_block')
    lathe(cv, 0, -13, 0, [9, 9, 7, 5, 3, 3, 3, 3, 3, 4, 6], 'quartz_block')
    ring(cv, 0, -13, 0, 9, 'gold_block')
    # tier 1 (hollow: a pantry inside)
    for y, m in ((1, SP), (2, SP), (3, CR), (4, SP)): disc(cv, 0, y, 0, 11, m, r_in=10)
    disc(cv, 0, 5, 0, 11, PK)
    cyl(cv, 0, 1, 4, 0, 3, lambda x, y, z: CR if y == 3 else SP)
    for a in range(0, 360, 9):                                      # frosting drips
        if cv.rng.random() < 0.55:
            x, z = round(11 * math.cos(math.radians(a))), round(11 * math.sin(math.radians(a)))
            for y in range(4, 4 - cv.rng.randint(1, 2), -1):
                if cv.get(x, y, z): cv.set(x, y, z, PK)
    for sx in (-1, 1):                                              # four doors on the diagonals
        for sz in (-1, 1):
            for x in range(5, 11):
                for z in range(5, 11):
                    if abs(x - z) <= 1 and 9.0 <= math.hypot(x, z) < 12:
                        for y in (1, 2, 3): cv.set(sx * x, y, sz * z, None)
    for k in range(4):                                              # ramps on the axes
        for i in range(5):
            r = 16 - i; y = 1 + i
            for w in (-1, 0, 1):
                x, z = rot_xz(r, w, k)
                cv.set(x, y, z, xform('quartz_stairs[facing=west,half=bottom]', k))
                for yy in range(1, y): cv.set(x, yy, z, 'smooth_quartz')
    # pantry furniture
    for k in range(4):
        for (x, y, z, s) in ((7, 1, 0, 'smooth_quartz_slab[type=top]'), (7, 2, 0, 'cake'), (8, 1, 2, 'barrel[facing=up]'), (8, 1, -2, 'hay_block[axis=y]'),
                             (8, 2, -2, 'pink_candle[candles=2,lit=true]'), (4, 1, 0, 'quartz_stairs[facing=west,half=bottom]')):
            xx, zz = rot_xz(x, z, k); cv.set(xx, y, zz, xform(s, k))
        xx, zz = rot_xz(6, 3, k); hang_lamp(cv, xx, 4, zz)
        xx, zz = rot_xz(6, -3, k); hang_lamp(cv, xx, 4, zz)
    for x in range(-9, 10):
        for z in range(-9, 10):
            if 3.6 <= math.hypot(x, z) < 6 and cv.empty(x, 1, z) and (x + z) % 2 == 0: cv.set(x, 1, z, 'pink_carpet')
    # tier 2 and 3
    for y, m in ((6, SP), (7, CR), (8, SP)): disc(cv, 0, y, 0, 6, m)
    disc(cv, 0, 9, 0, 6, CR)
    for y, m in ((10, SP), (11, SP)): disc(cv, 0, y, 0, 3, m)
    disc(cv, 0, 12, 0, 3, PK)
    for a in range(0, 360, 45):                                     # strawberries round tier 2, candles round tier 1
        x, z = round(5 * math.cos(math.radians(a + 22))), round(5 * math.sin(math.radians(a + 22)))
        cv.set(x, 10, z, 'red_concrete'); cv.set(x, 11, z, leaf('azalea_leaves'))
    for i, a in enumerate(range(0, 360, 60)):
        x, z = round(9.5 * math.cos(math.radians(a + 30))), round(9.5 * math.sin(math.radians(a + 30)))
        if abs(abs(x) - 6) <= 1 and abs(abs(z) - 6) <= 1: continue
        col = ('light_blue', 'yellow', 'magenta', 'lime', 'orange', 'purple')[i]
        cv.set(x, 6, z, col + '_concrete'); cv.set(x, 7, z, col + '_concrete'); cv.set(x, 8, z, 'torch')
    sphere(cv, 0, 14, 0, 1.6, 'red_concrete'); cv.set(0, 16, 0, 'dark_oak_fence'); cv.set(0, 17, 0, 'dark_oak_fence'); cv.set(1, 17, 0, leaf('oak_leaves'))
    for sx in (-1, 1):
        for sz in (-1, 1):
            gen_pad(cv, sx * 6, 5, sz * 6, 'emerald', frame=PK); gem_marker(cv, sx * 6, 5, sz * 6, 'emerald')
    return cv

def macaron(col):
    cv = Canvas(sum(map(ord, col)))
    A = col + '_concrete'; Bm = col + '_terracotta'
    for y, r, m in ((0, 6, A), (-1, 7, A), (-2, 7, Bm), (-3, 6, 'white_concrete'), (-4, 7, Bm), (-5, 7, A), (-6, 6, A), (-7, 4, A)):
        disc(cv, 0, y, 0, r, m)
    gen_pad(cv, 0, 0, 0, 'diamond', frame=A); gem_marker(cv, 0, 0, 0, 'diamond')
    return cv

def donut(col):
    cv = Canvas(sum(map(ord, col)) + 5)
    torus(cv, 0, -2, 0, 5, 2.4, lambda x, y, z: (col + '_concrete') if y >= -2 else 'orange_terracotta', ry=2)
    sp = ('yellow_concrete', 'white_concrete', 'lime_concrete', 'light_blue_concrete', 'pink_concrete')
    for (x, y, z), s in list(cv.b.items()):
        if y >= -1 and cv.empty(x, y + 1, z) and cv.rng.random() < 0.16: cv.set(x, y, z, cv.rng.choice(sp))
    return cv

def xform(s, k):
    from canvas import xform_state
    return xform_state(s, k)

def build():
    mb = MapBuilder(101)
    mb.put(cake(), 0, 0, kind='mid')
    mb.bases(cup_base, 60, 22.5)
    for i, col in enumerate(('magenta', 'light_blue', 'orange', 'purple')):
        a = math.radians(90 * i); mb.put(macaron(col), round(36 * math.cos(a)), round(36 * math.sin(a)), kind='diamond')
    for i, col in enumerate(('brown', 'magenta', 'light_blue', 'white')):
        a = math.radians(45 + 90 * i); mb.put(donut(col), round(37 * math.cos(a)), round(37 * math.sin(a)), y=3, kind='extra')
    return mb

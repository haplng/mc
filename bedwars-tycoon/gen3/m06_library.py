"""Map 6 - 도서관: stacks of giant books round a reading table with an open book; four curved walls of shelves carry the diamonds."""
import math
from canvas import Canvas
from kit import *

ID = 'library'; NAME = '도서관'
GATE = dict(frame='dark_oak_planks', roof_full='bookshelf', plaza='spruce_planks', glass='orange_stained_glass')
PAGE = lambda x, y, z: 'smooth_quartz' if y % 2 else 'calcite'
NEUTRAL = ['brown_terracotta', 'gray_terracotta', 'green_terracotta', 'purple_terracotta', 'black_terracotta', 'orange_terracotta', 'light_gray_terracotta']

def book(cv, x0, z0, x1, z1, y0, y1, cover, spine='x0'):
    """a closed book lying flat: covers on top and bottom, pages between (set back one block on the three open sides)"""
    box(cv, x0, y0, z0, x1, y0, z1, cover); box(cv, x0, y1, z0, x1, y1, z1, cover)
    a, b, c, d = x0 + 1, z0 + 1, x1 - 1, z1 - 1
    if spine == 'x0': a = x0
    elif spine == 'x1': c = x1
    elif spine == 'z0': b = z0
    else: d = z1
    if y1 - y0 > 1:
        box(cv, a, y0 + 1, b, c, y1 - 1, d, PAGE)
        if spine == 'x0': box(cv, x0, y0, z0, x0, y1, z1, cover)
        elif spine == 'x1': box(cv, x1, y0, z0, x1, y1, z1, cover)
        elif spine == 'z0': box(cv, x0, y0, z0, x1, y1, z0, cover)
        else: box(cv, x0, y0, z1, x1, y1, z1, cover)

def upright(cv, x0, x1, z0, z1, y0, y1, cover):
    """a book standing on a shelf (spine at z0, facing away from the reader)"""
    box(cv, x0, y0, z0, x1, y1, z1, cover)
    if x1 - x0 >= 2:
        box(cv, x0 + 1, y1, z0 + 1, x1 - 1, y1, z1, 'smooth_quartz'); box(cv, x0 + 1, y0, z1, x1 - 1, y1, z1, PAGE)
    for y in (y0 + 2, y1 - 2): box(cv, x0, y, z0, x1, y, z0, 'gold_block')

def book_base(dye):
    cv = Canvas(sum(map(ord, dye)) + 6)
    T = dye + '_concrete'
    book(cv, -12, -15, 12, 15, -3, 0, T, 'x0')
    for z in range(-15, 16): cv.set(-13, -1, z, T); cv.set(-13, -2, z, T)
    for x in range(-10, 11):                                            # gilt frame on the cover
        for z in range(-13, 14):
            if (abs(x) == 10 or abs(z) == 13): cv.set(x, 0, z, 'yellow_terracotta')
    for sx in (-10, 10):
        for sz in (-13, 13): cv.set(sx, 0, sz, 'gold_block')
    book(cv, -10, -13, 13, 12, -7, -4, 'brown_terracotta', 'x1'); book(cv, -12, -10, 9, 14, -10, -8, 'gray_terracotta', 'z0')
    book(cv, -7, -8, 6, 8, -12, -11, 'green_terracotta', 'x0')
    # the book house
    box(cv, -8, 1, -14, 8, 5, -5, PAGE, hollow=True); box(cv, -7, 1, -13, 7, 5, -6, None)
    box(cv, -8, 6, -14, 8, 6, -4, 'brown_terracotta'); box(cv, -8, 1, -14, 8, 6, -14, 'brown_terracotta')
    for x in (-8, 8):
        for y in range(1, 6): cv.set(x, y, -5, 'brown_terracotta')
    for y in (2, 4): box(cv, -8, y, -14, 8, y, -14, 'gold_block') if y == 4 else None
    for x in (-1, 0, 1):
        for y in (1, 2, 3): cv.set(x, y, -5, None)
    for x in (-2, 2):
        for y in (1, 2, 3): cv.set(x, y, -5, 'dark_oak_planks')
    for x in (-2, -1, 0, 1, 2): cv.set(x, 4, -5, 'dark_oak_planks')
    gen_pad(cv, 0, 0, -10, 'iron', frame='dark_oak_planks')
    for x in list(range(-7, -2)) + list(range(3, 8)):
        for y in (1, 2, 3): cv.set(x, y, -13, 'bookshelf')
    cv.set(0, 1, -13, 'lectern[facing=south]'); cv.set(-6, 1, -12, 'enchanting_table'); cv.set(6, 1, -12, 'cartography_table')
    # the shopkeepers stand in niches framed with bookshelves, each behind a desk
    for sx in (-1, 1):
        for z in (-9, -7):
            for y in (1, 2, 3): cv.set(sx * 7, y, z, 'bookshelf')
        for z in (-9, -8, -7): cv.set(sx * 7, 4, z, 'dark_oak_planks')
        cv.set(sx * 6, 1, -8, 'dark_oak_planks')
    cv.set(-7, 1, -10, 'chest[facing=east]'); cv.set(7, 1, -10, 'ender_chest[facing=west]')
    for x in (-4, 4): hang_lamp(cv, x, 5, -9)
    for x in range(-2, 3):
        for z in (-8, -7): cv.set(x, 1, z, dye + '_carpet', force=False)
    # books standing on top of it, a quill, a candle, the ribbon
    cols = [c for c in NEUTRAL]; cv.rng.shuffle(cols)
    x = -8; i = 0
    while x < 7:
        w = cv.rng.choice((2, 3, 3)); h = cv.rng.randint(6, 11)
        if x + w - 1 > 8: w = 8 - x + 1
        upright(cv, x, x + w - 1, -13 + cv.rng.randint(0, 1), -7, 7, 7 + h, T if i == 2 else cols[i % len(cols)])
        x += w; i += 1
    for (px, py, pz) in ((9, 1, 11), (10, 1, 11), (9, 1, 10), (10, 1, 10), (9, 2, 11), (10, 2, 11), (9, 2, 10), (10, 2, 10)): cv.set(px, py, pz, 'black_concrete')
    line(cv, (9, 3, 10), (11, 13, 6), 'white_wool')
    for i, (px, py, pz) in enumerate(((10, 8, 9), (10, 9, 8), (11, 10, 8), (11, 11, 7), (11, 12, 7), (10, 10, 7), (10, 11, 6), (12, 12, 6))): cv.set(px, py, pz, 'white_wool')
    cv.set(-9, 1, 11, 'gold_block')
    for y in (2, 3, 4, 5): cv.set(-9, y, 11, 'white_concrete')
    cv.set(-9, 6, 11, 'white_candle[candles=1,lit=true]')
    for x in (5, 6):
        for y in range(-7, 0): cv.set(x, y, 16, dye + '_wool')
    cv.set(5, -8, 16, dye + '_wool')
    bed(cv, dye, 0, 1, 9)
    team_markers(cv, dye, spawn=(0, 1, -7), bedpos=(0, 1, 9), gen=(0, 0, -10), shop=(-7, 1, -8), upg=(7, 1, -8))
    return cv

def table():
    cv = Canvas(66)
    Dk = 'dark_oak_planks'
    disc(cv, 0, 0, 0, 26, lambda x, y, z: Dk if (math.hypot(x, z) >= 24.5 or 12.5 <= math.hypot(x, z) < 13.5) else 'spruce_planks')
    disc(cv, 0, -1, 0, 26, Dk); disc(cv, 0, -2, 0, 24, 'spruce_planks'); disc(cv, 0, -3, 0, 22, Dk, r_in=18)
    lathe(cv, 0, -17, 0, [13, 12, 9, 7, 6, 5, 5, 6, 5, 5, 5, 6, 8, 11, 15], lambda x, y, z: Dk if y % 3 else 'stripped_dark_oak_wood')
    for k in range(4):
        x, z = rot_xz(11, 11, k)
        for i in range(3): box(cv, x - 2 + i * (1 if x > 0 else -1) // 1 * 0, -17 - i, z - 2, x + 2, -17 - i, z + 2, Dk) if i == 0 else None
    # the open book
    box(cv, -20, 1, -16, 20, 1, 16, 'brown_terracotta')
    for sx in (-1, 1):
        box(cv, sx * 1, 2, -15, sx * 18, 2, 15, 'smooth_quartz'); box(cv, sx * 1, 3, -15, sx * 17, 3, 15, 'white_concrete'); box(cv, sx * 19, 2, -15, sx * 19, 2, 15, 'calcite')
    for z in range(-15, 16): cv.set(0, 2, z, 'brown_terracotta')
    for sx in (-1, 1):                                                  # lines of text
        for z in range(-12, 13, 2):
            x = 3
            while x < 16:
                n = cv.rng.randint(2, 5)
                for i in range(n):
                    if x + i < 16 and not (sx < 0 and z < -7 and x + i > 12): cv.set(sx * (x + i), 3, z, 'gray_concrete')
                x += n + 1
    box(cv, -16, 3, -13, -13, 3, -10, 'red_concrete'); cv.set(-15, 3, -12, 'gold_block'); cv.set(-14, 3, -11, 'gold_block')
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * 9, sz * 7
            gen_pad(cv, x, 3, z, 'emerald', frame='white_concrete'); gem_marker(cv, x, 3, z, 'emerald')
    # things on the table: candles, a stack of books, an ink pot, steps up onto the book
    for (x, z) in ((-21, 12), (21, -12)):
        disc(cv, x, 1, z, 2, 'gold_block'); cyl(cv, x, 2, 8, z, 1, 'white_concrete'); cv.set(x, 9, z, 'white_candle[candles=1,lit=true]')
    book(cv, 14, 18, 22, 23, 1, 3, 'purple_terracotta', 'z0') if False else None
    book(cv, -6, 19, 5, 24, 1, 3, 'green_terracotta', 'z1'); book(cv, -4, 19, 6, 23, 4, 5, 'orange_terracotta', 'x0')
    cyl(cv, 0, 1, 4, -21, 2.2, 'black_concrete'); disc(cv, 0, 4, -21, 1.2, 'blue_concrete'); line(cv, (1, 5, -21), (5, 15, -23), 'white_wool')
    for i, (x, y, z) in enumerate(((3, 9, -22), (4, 11, -22), (4, 12, -23), (5, 13, -22), (3, 10, -23))): cv.set(x, y, z, 'white_wool')
    for k in range(4):
        for i, (d, y) in enumerate(((22, 1), (21, 2))):
            for w in (-1, 0, 1):
                x, z = rot_xz(d if k % 2 == 0 else d - 4, w, k)
                cv.set(x, y, z, xs('spruce_stairs[facing=west,half=bottom]', k))
    return cv

def arc(i, d=0):
    """a curved wall of shelves with a gallery; local +x is outwards; d moves the whole arc outwards"""
    cv = Canvas(67 + i)
    Dk = 'dark_oak_planks'
    zb = int((63 + d) * math.sin(math.radians(25))) + 3
    for x in range(40 + d, 67 + d):
        for z in range(-zb, zb + 1):
            r = math.hypot(x + 0.0, z) - d; a = math.degrees(math.atan2(z, x))
            if not (47.5 <= r < 62.5 and abs(a) <= 25): continue
            edge = r < 48.5 or r >= 61.5 or abs(a) > 24
            cv.set(x, 0, z, Dk if edge else ('spruce_planks' if int(r) % 4 else 'stripped_spruce_wood')); cv.set(x, -1, z, Dk)
            if 50 <= r < 60 and abs(a) <= 22:
                cv.set(x, -2, z, 'spruce_planks'); cv.set(x, -3, z, 'spruce_planks')
            if 52.5 <= r < 57.5 and abs(a) <= 19:
                cv.set(x, -4, z, Dk); cv.set(x, -5, z, Dk)
            if 54 <= r < 56 and abs(a) <= 15: cv.set(x, -6, z, 'spruce_planks')
            if r >= 60.5:                                               # the wall of books
                post = int((a + 25) * 1.2) % 6 == 0
                for y in range(1, 11):
                    cv.set(x, y, z, Dk if (post or y in (5, 10)) else 'bookshelf')
                cv.set(x, 11, z, 'dark_oak_slab[type=bottom]')
            elif 57.5 <= r < 60.5:                                      # gallery
                cv.set(x, 5, z, 'spruce_planks')
                if r < 58.5: cv.set(x, 6, z, 'dark_oak_fence')
                if abs(a) > 23.2 and r >= 58.5: cv.set(x, 6, z, 'dark_oak_fence')
            if 48.5 <= r < 49.5 and int(abs(a)) in (8, 20):
                for y in (1, 2, 3): cv.set(x, y, z, 'dark_oak_fence')
                cv.set(x, 4, z, 'lantern[hanging=false]')
            if 59 <= r < 60 and int(abs(a) * 10) % 60 == 30: hang_lamp(cv, x, 4, z)
    # ladder up to the gallery at one end, reading desk in the middle, the generator
    for y in range(1, 6): cv.set(53 + d, y, 24, 'dark_oak_log[axis=y]')
    for y in range(1, 6): cv.set(52 + d, y, 24, 'ladder[facing=west]')
    cv.set(52 + d, 5, 24, 'ladder[facing=west]'); cv.set(54 + d, 5, 24, 'spruce_planks'); cv.set(54 + d, 5, 25, 'spruce_planks')
    for z in (-3, -2, -1, 0, 1, 2, 3):
        cv.set(56 + d, 1, z, 'dark_oak_slab[type=top]') if abs(z) != 3 else cv.set(56 + d, 1, z, 'dark_oak_planks')
    cv.set(56 + d, 2, 0, 'lectern[facing=west]'); cv.set(56 + d, 2, -2, 'lantern[hanging=false]'); cv.set(56 + d, 2, 2, 'flower_pot')
    cv.set(54 + d, 1, 0, 'spruce_stairs[facing=east,half=bottom]')
    for x in (52 + d, 53 + d, 54 + d, 55 + d):
        for z in (-2, -1, 0, 1, 2):
            if cv.empty(x, 1, z): cv.set(x, 1, z, 'red_carpet')
    for (x, z) in ((57 + d, -9), (57 + d, 9)): box(cv, x, 1, z - 1, x + 1, 2, z + 1, 'bookshelf'); cv.set(x, 3, z, 'bookshelf')
    gen_pad(cv, 50 + d, 0, 0, 'diamond', frame='dark_oak_planks'); gem_marker(cv, 50 + d, 0, 0, 'diamond')
    return cv

def flying_book(i):
    cv = Canvas(69 + i)
    col = ('purple_terracotta', 'orange_terracotta', 'green_terracotta', 'brown_terracotta')[i % 4]
    for dx in range(-5, 6):
        y = (abs(dx) + 1) // 2
        for z in range(-3, 4):
            cv.set(dx, y - 1, z, col)
            if abs(z) < 3 and abs(dx) < 5: cv.set(dx, y, z, 'smooth_quartz' if dx else col)
    return cv

def build():
    mb = MapBuilder(606)
    mb.put(table(), 0, 0, kind='mid')
    for k in range(4): mb.put(arc(k, 0), 0, 0, k=k, kind='diamond')
    mb.bases(book_base, 100, 16)
    for k in range(4):
        x, z = rot_xz(53, 53, k); mb.put(flying_book(k), x, z, y=7, k=k, kind='extra')
    return mb

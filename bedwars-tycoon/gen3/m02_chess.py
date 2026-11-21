"""Map 2 - 체스: rook towers on checkered tiles along the four sides of a giant chessboard with a game in progress."""
import math
from canvas import Canvas
from kit import *

ID = 'chess'; NAME = '체스'
GATE = dict(frame='polished_blackstone_bricks', roof_full='smooth_quartz', plaza='quartz_bricks', glass='white_stained_glass')
DARK = {'blue', 'yellow', 'white', 'gray'}          # which teams play the black pieces

def rook_base(dye):
    cv = Canvas(sum(map(ord, dye)) + 2)
    dark = dye in DARK; T = dye + '_concrete'
    body = 'polished_blackstone_bricks' if dark else 'quartz_bricks'; trim = 'polished_blackstone' if dark else 'smooth_quartz'
    pc = 'polished_blackstone' if dark else 'smooth_quartz'
    # tile
    box(cv, -11, 0, -14, 11, 0, 14, 'dark_oak_planks')
    box(cv, -10, 0, -13, 10, 0, 13, checker('light_gray_concrete' if dye == 'white' else 'white_concrete', T, 3, ox=-10, oz=-13))
    under_steps(cv, -11, -14, 11, 14, 0, 6, ['dark_oak_planks', 'spruce_planks', 'spruce_planks', 'dark_oak_planks', 'spruce_planks', 'dark_oak_planks'])
    cv.set(0, -7, 0, 'iron_chain[axis=y]'); cv.set(0, -8, 0, 'lantern[hanging=true]')
    for sx in (-11, 11):
        for sz in (-14, 14): cv.set(sx, 0, sz, 'gold_block')
    # rook tower
    cx, cz = 0, -7
    for y in range(1, 13):
        r = 6.5 if y in (1, 2, 11, 12) else 5.5
        m = trim if y in (1, 2, 11, 12) else (T if y == 10 else body)
        disc(cv, cx, y, cz, r, m, r_in=r - 1)
    for a in range(0, 360, 45):
        for da in (-8, 0, 8):
            x, z = cx + round(6.4 * math.cos(math.radians(a + da))), cz + round(6.4 * math.sin(math.radians(a + da)))
            cv.set(x, 13, z, trim)
    disc(cv, cx, 7, cz, 4.6, 'spruce_planks'); disc(cv, cx, 11, cz, 5.6, 'stone_bricks' if dark else 'smooth_quartz')
    for y in (1, 2):
        for x in (-1, 0, 1): cv.set(x, y, -12, trim)
    for y in range(1, 12): cv.set(0, y, -11, 'ladder[facing=south]')
    for x in (-1, 0, 1):                                              # door
        for y in (1, 2, 3):
            for z in (-3, -2, -1, 0): cv.set(x, y, z, None)
    for x in (-2, 2):
        for y in (1, 2, 3): cv.set(x, y, -1, T)
    for x in (-2, -1, 0, 1, 2): cv.set(x, 4, -1, T)
    for sx in (-1, 1):                                                # arrow slits
        for y in (4, 5, 8, 9): cv.set(sx * 5, y, cz, None)
    # inside
    gen_pad(cv, 0, 0, -8, 'iron', frame='polished_andesite')
    cv.set(-3, 1, -9, 'chest[facing=east]'); cv.set(3, 1, -9, 'ender_chest[facing=west]')
    hang_lamp(cv, -2, 6, -6); hang_lamp(cv, 2, 6, -6)
    for x, z, s in ((-3, -5, 'bookshelf'), (3, -5, 'barrel[facing=up]'), (-3, -10, 'crafting_table')):
        cv.set(x, 8, z, s)
    cv.set(3, 8, -9, 'bookshelf'); cv.set(3, 9, -9, 'bookshelf'); cv.set(-2, 8, -7, dye + '_carpet'); cv.set(-1, 8, -7, dye + '_carpet'); cv.set(0, 8, -7, dye + '_carpet')
    cv.set(1, 8, -6, 'lantern[hanging=false]')
    flag(cv, 0, 12, -7, 6, dye, d=(1, 0), pole='dark_oak_fence')
    # pawns guarding the bed, stalls
    for sx in (-1, 1): chess_piece(cv, sx * 8, 1, 11, 'pawn', pc)
    # the shopkeepers stand in the alcove under the tower wall, each behind a counter in the team colour
    for sx in (-1, 1):
        for y in (1, 2): cv.set(sx * 5, y, -8, body); cv.set(sx * 5, y, -6, body)
        cv.set(sx * 5, 3, -7, None)                                       # head room for the name: the arrow slit above starts one block lower
        cv.set(sx * 4, 1, -7, T)
    bed(cv, dye, 0, 1, 9)
    team_markers(cv, dye, spawn=(0, 1, -4), bedpos=(0, 1, 9), gen=(0, 0, -8), shop=(-5, 1, -7), upg=(5, 1, -7))
    return cv

def board():
    cv = Canvas(22)
    L = 'stripped_birch_wood'; D = 'dark_oak_planks'; F = 'spruce_planks'
    Wm = 'smooth_quartz'; Bm = 'polished_blackstone'
    # the case under the board (a hall with captured pieces)
    box(cv, -22, -7, -22, 21, 0, 21, F, hollow=True)
    box(cv, -22, 0, -22, 21, 0, 21, F); box(cv, -20, 0, -20, 19, 0, 19, checker(L, D, 5, ox=-20, oz=-20))
    for sx in (-22, 21):
        for sz in (-22, 21):
            for y in range(-7, 1): cv.set(sx, y, sz, 'dark_oak_log[axis=y]')
            cv.set(sx, 0, sz, 'gold_block')
    box(cv, -22, -4, -22, 21, -4, 21, 'dark_oak_planks', hollow=True)
    for x in range(-22, 22):
        for z in range(-22, 22):
            if (x in (-22, 21) or z in (-22, 21)) and (x + z) % 3 == 0 and -19 < min(x, z) and max(x, z) < 18: cv.set(x, -4, z, 'glass_pane') if False else cv.set(x, -4, z, 'white_stained_glass')
    box(cv, -21, -6, -21, 20, -1, 20, None)
    box(cv, -22, -1, -22, 21, -1, 21, 'dark_oak_planks')
    under_steps(cv, -22, -22, 21, 21, -7, 5, ['dark_oak_planks', 'spruce_planks'], inset=3)
    cv.set(0, -13, 0, 'iron_chain[axis=y]'); cv.set(0, -14, 0, 'lantern[hanging=true]')
    for x in (-13, -3, 2, 12):
        for z in (-13, -3, 2, 12):
            for y in range(-6, -1): cv.set(x, y, z, 'dark_oak_log[axis=y]')
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if cv.rng.random() < 0.6: hang_lamp(cv, x + dx, -2, z + dz)
    for i in range(-20, 20):
        for j in (-1, 0):
            cv.set(i, -6, j, 'red_carpet', force=False); cv.set(j, -6, i, 'red_carpet', force=False)
    # captured pieces lying about, crates
    for (x, z, m, ax) in ((-16, -15, Wm, 'x'), (10, -16, Bm, 'z'), (-15, 12, Bm, 'x'), (13, 13, Wm, 'z'), (8, 8, Wm, 'x'), (-9, -8, Bm, 'z')):
        for i in range(6):
            r = (1.6, 1.2, 0.8, 0.8, 1.2, 1.4)[i]
            if ax == 'x': vdisc(cv, x + i, -5, z, r, m, axis='x')
            else: vdisc(cv, x, -5, z + i, r, m, axis='z')
    for (x, z) in ((-20, -8), (-20, 7), (19, -9), (19, 6), (-8, -20), (7, -20), (-9, 19), (6, 19)):
        crates(cv, x if abs(x) < 19 else (x + (1 if x < 0 else -1)), -6, z if abs(z) < 19 else (z + (1 if z < 0 else -1)), 4)
    for (x, z) in ((-21, -15), (-21, 14), (20, -16), (20, 13)):
        for y in (-6, -5, -4): cv.set(x + (1 if x < 0 else -1), y, z, 'bookshelf'); cv.set(x + (1 if x < 0 else -1), y, z + 1, 'bookshelf')
    # four stair porches (one in the middle of each side)
    for k in range(4):
        for i in range(7):                                    # steps climb along the wall from the landing up to the frame
            y = -6 + i
            for w in (23, 24):
                x, z = rot_xz(w, -5 + i + 2, k)
                cv.set(x, y, z, xs('spruce_stairs[facing=south,half=bottom]', k))
                for yy in range(-7, y): cv.set(x, yy, z, F)
        for w in (22, 23, 24, 25):                            # landing in front of the doorway, and the doorway
            for d in (-5, -4, -3):
                x, z = rot_xz(w, d, k)
                if w > 22: cv.set(x, -7, z, 'dark_oak_planks')
                else:
                    for y in (-6, -5, -4): cv.set(x, y, z, None)
        for d in (-6, -2):
            x, z = rot_xz(25, d, k); cv.set(x, -7, z, 'dark_oak_planks'); cv.set(x, -6, z, 'spruce_fence'); cv.set(x, -5, z, 'lantern[hanging=false]')
        for d in range(-6, 5):
            x, z = rot_xz(25, d, k)
            if cv.empty(x, -7, z): cv.set(x, -7, z, 'dark_oak_planks' if d < -1 else None)
        x, z = rot_xz(23, 4, k); cv.set(x, 0, z, F); x, z = rot_xz(24, 4, k); cv.set(x, 0, z, F)
        for d in (4,):
            for w in (23, 24):
                x, z = rot_xz(w, d, k)
                for yy in range(-7, 0): cv.set(x, yy, z, F)
    # the game
    sq = lambda i, j: (-18 + 5 * i, -18 + 5 * j)
    game = [('king', 4, 0, 0), ('queen', 3, 1, 0), ('rook', 0, 0, 0), ('rook', 7, 0, 0), ('bishop', 5, 1, 0), ('knight', 1, 2, 0), ('pawn', 0, 2, 0),
            ('pawn', 6, 2, 0), ('pawn', 3, 3, 0), ('king', 3, 7, 1), ('queen', 4, 6, 1), ('rook', 0, 7, 1), ('rook', 7, 7, 1), ('bishop', 2, 6, 1),
            ('knight', 6, 5, 1), ('pawn', 1, 5, 1), ('pawn', 7, 5, 1), ('pawn', 4, 4, 1)]
    for kind, i, j, c in game:
        x, z = sq(i, j); chess_piece(cv, x, 1, z, kind, Bm if c else Wm, trim='gold_block' if kind in ('king', 'queen') else None)
    for i, j in ((2, 2), (5, 2), (2, 5), (5, 5)):
        x, z = sq(i, j); gen_pad(cv, x, 0, z, 'emerald', frame='smooth_quartz'); gem_marker(cv, x, 0, z, 'emerald')
    return cv

def gem_tile(i):
    cv = Canvas(40 + i)
    box(cv, -5, 0, -5, 5, 0, 5, 'dark_oak_planks'); box(cv, -4, 0, -4, 4, 0, 4, checker('white_concrete', 'black_concrete', 3, ox=-4, oz=-4))
    under_steps(cv, -5, -5, 5, 5, 0, 4, ['dark_oak_planks', 'spruce_planks'], inset=1)
    under_steps(cv, -2, -2, 2, 2, -4, 2, ['spruce_planks', 'dark_oak_planks'], inset=1)
    gen_pad(cv, 0, 0, 0, 'diamond', frame='smooth_quartz'); gem_marker(cv, 0, 0, 0, 'diamond')
    chess_piece(cv, -3, 1, -3, 'pawn', 'smooth_quartz', f=0.6); chess_piece(cv, 3, 1, 3, 'pawn', 'polished_blackstone', f=0.6)
    return cv

def bishop_tile(i):
    cv = Canvas(50 + i)
    box(cv, -4, 0, -4, 4, 0, 4, 'dark_oak_planks'); box(cv, -3, 0, -3, 3, 0, 3, 'white_concrete' if i % 2 else 'black_concrete')
    under_steps(cv, -4, -4, 4, 4, 0, 4, ['dark_oak_planks', 'spruce_planks'], inset=1)
    chess_piece(cv, 0, 1, 0, 'bishop' if i % 2 else 'knight', 'polished_blackstone' if i % 2 else 'smooth_quartz', f=1.3 if i % 2 else 1.0, trim='gold_block')
    return cv

def build():
    mb = MapBuilder(202)
    mb.put(board(), 0, 0, kind='mid')
    spots = []
    for q in range(4):
        for sgn in (-1, 1):
            x, z = rot_xz(64, sgn * 22, q); spots.append((x, z, (q + 1) % 4, sgn > 0))
    mb.bases_at(rook_base, spots)
    for q in range(4):
        x, z = rot_xz(37, 0, q); mb.put(gem_tile(q), x, z, kind='diamond')
        x, z = rot_xz(58, 58, q); mb.put(bishop_tile(q), x, z, y=2, kind='extra')
    return mb

"""The lobby (built from scratch for v5): a forest island with a castle wall whose five arched gates lead to the maps,
and BED WARS in big white block letters floating above the wall, straight ahead of the spawn."""
import math
from nbtlib import Compound, String, Byte, List
from canvas import Canvas
from kit import *
import m03_circus, m06_library

TH = dict(top=[('grass_block', 9), ('moss_block', 1), ('podzol', 1)], sub=[('dirt', 3), ('coarse_dirt', 1)], sub_n=4,
          under=[('stone', 5), ('andesite', 2), ('tuff', 1), ('cobblestone', 1)], tip=[('cobbled_deepslate', 2), ('deepslate', 1), ('tuff', 1)],
          strata=['stone', 'stone', 'andesite', 'stone', 'tuff', 'stone', 'cobblestone', 'deepslate'])
WALL = [('stone_bricks', 7), ('cracked_stone_bricks', 1), ('mossy_stone_bricks', 1), ('andesite', 1)]
PAVE = [('stone_bricks', 4), ('andesite', 2), ('cobblestone', 2), ('polished_andesite', 1)]
DYES = ['red', 'blue', 'lime', 'yellow', 'cyan', 'white', 'pink', 'gray']
GATE_X = (-30, -15, 0, 15, 30)
WZ0, WZ1 = -28, -24                       # the wall occupies these z; its front face looks towards +z (the spawn)

FONT = {'B': ['XXXXXX.', 'XX...XX', 'XX...XX', 'XX...XX', 'XXXXXX.', 'XX...XX', 'XX...XX', 'XX...XX', 'XXXXXX.'],
        'E': ['XXXXXXX', 'XX.....', 'XX.....', 'XX.....', 'XXXXXX.', 'XX.....', 'XX.....', 'XX.....', 'XXXXXXX'],
        'D': ['XXXXX..', 'XX..XX.', 'XX...XX', 'XX...XX', 'XX...XX', 'XX...XX', 'XX...XX', 'XX..XX.', 'XXXXX..'],
        'W': ['XX...XX', 'XX...XX', 'XX...XX', 'XX...XX', 'XX.X.XX', 'XX.X.XX', 'XXXXXXX', 'XXX.XXX', 'XX...XX'],
        'A': ['..XXX..', '.XX.XX.', 'XX...XX', 'XX...XX', 'XXXXXXX', 'XX...XX', 'XX...XX', 'XX...XX', 'XX...XX'],
        'R': ['XXXXXX.', 'XX...XX', 'XX...XX', 'XX...XX', 'XXXXXX.', 'XX.XX..', 'XX..XX.', 'XX...XX', 'XX...XX'],
        'S': ['.XXXXX.', 'XX...XX', 'XX.....', 'XX.....', '.XXXXX.', '.....XX', '.....XX', 'XX...XX', '.XXXXX.']}

def title(cv, y, z, text='BED WARS', scale=1, gap=2, space=6):
    """white block letters in the x-y plane (readable from +z), centred on x=0; bottom row at y"""
    words = text.split(' ')
    w = sum(len(wd) * 7 + (len(wd) - 1) * gap for wd in words) * scale + (len(words) - 1) * space * scale
    x = -(w // 2)
    for ch in text:
        if ch == ' ': x += (space - gap) * scale; continue
        for r, row in enumerate(FONT[ch]):
            for c, bit in enumerate(row):
                if bit != 'X': continue
                for i in range(scale):
                    for j in range(scale):
                        px, py = x + c * scale + i, y + (8 - r) * scale + j
                        cv.set(px, py, z, 'white_concrete'); cv.set(px, py, z - 1, 'white_concrete'); cv.set(px, py, z - 2, 'light_gray_concrete')
                        if (px + py) % 3 == 0: cv.set(px, py, z + 1, 'light[level=15]')          # invisible light, so the letters stay white at night
        x += (7 + gap) * scale
    return w

def sign(cv, x, y, z, lines, rotation=0, wood='spruce'):
    msgs = []
    for i in range(4):
        t, c = lines[i] if i < len(lines) else ('', 'black')
        msgs.append(Compound({'text': String(t), 'color': String(c)}))
    side = lambda m: Compound({'messages': List[Compound](m), 'has_glowing_text': Byte(1), 'color': String('black')})
    blank = [Compound({'text': String('')}) for _ in range(4)]
    cv.set(x, y, z, f'{wood}_sign[rotation={rotation % 16}]')
    cv.nbt[(x, y, z)] = Compound({'id': String('minecraft:sign'), 'front_text': side(msgs), 'back_text': side(blank), 'is_waxed': Byte(1)})

def wall_sign(cv, x, y, z, lines, facing='south', wood='spruce'):
    """a sign hanging on the block behind it; it looks towards `facing`"""
    msgs = []
    for i in range(4):
        t, c = lines[i] if i < len(lines) else ('', 'black')
        msgs.append(Compound({'text': String(t), 'color': String(c)}))
    side = lambda m: Compound({'messages': List[Compound](m), 'has_glowing_text': Byte(1), 'color': String('black')})
    blank = [Compound({'text': String('')}) for _ in range(4)]
    cv.set(x, y, z, f'{wood}_wall_sign[facing={facing}]')
    cv.nbt[(x, y, z)] = Compound({'id': String('minecraft:sign'), 'front_text': side(msgs), 'back_text': side(blank), 'is_waxed': Byte(1)})

HALL = dict(x0=-28, x1=-18, z0=18, z1=26, zc=22)     # the upgrade shop: outer walls; its door looks east, towards the spawn plaza
UNLOCK_NPC = (-25, 1, 22, -90.0)                        # where its keeper stands (lobby coordinates) and the way it looks
SOFT = ('short_grass', 'fern', 'large_fern', 'poppy', 'dandelion', 'oxeye_daisy', 'cornflower')

def upgrade_hall(cv):
    """the upgrade shop west of the spawn plaza: a half-timbered cabin with a dark roof; the keeper stands behind a counter that runs
    from wall to wall. Built last and without the canvas' random numbers, so the rest of the lobby stays exactly as it was."""
    import random
    rng = random.Random(4107)
    X0, X1, Z0, Z1, zc = HALL['x0'], HALL['x1'], HALL['z0'], HALL['z1'], HALL['zc']
    for x in range(X0 - 1, X1 + 2):                                     # nothing woody may stand where the cabin and its eaves go
        for z in range(Z0 - 1, Z1 + 2):
            for y in range(1, 12):
                n = cv.name(x, y, z)
                assert n is None or n in SOFT, ('the upgrade shop would cut into', n, (x, y, z))
    def clear_plants(x, z):
        for y in (1, 2):
            if cv.name(x, y, z) in SOFT: cv.set(x, y, z, None)
    # --- the way from the plaza: the west bench makes room for it
    for z in (zc - 1, zc, zc + 1): cv.set(-8, 1, z, None)
    for x in range(X1 + 1, -9):
        for z in (zc - 1, zc, zc + 1):
            if cv.name(x, 0, z) in ('grass_block', 'moss_block', 'podzol'):
                clear_plants(x, z); cv.set(x, 0, z, rng.choice(['stone_bricks'] * 4 + ['andesite'] * 2 + ['cobblestone'] * 2 + ['polished_andesite']))
    # --- floor and walls
    post = 'stripped_spruce_log[axis=y]'
    for x in range(X0 - 1, X1 + 2):
        for z in range(Z0 - 1, Z1 + 2): clear_plants(x, z)
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            edge = x in (X0, X1) or z in (Z0, Z1)
            cv.set(x, 0, z, 'stone_bricks' if edge else 'spruce_planks')
            if not edge: continue
            corner = x in (X0, X1) and z in (Z0, Z1)
            is_post = corner or (z in (Z0, Z1) and x == (X0 + X1) // 2) or (x in (X0, X1) and z in (zc - 2, zc + 2))
            for y in (1, 2, 3):
                cv.set(x, y, z, post if is_post else (rng.choice(['stone_bricks'] * 7 + ['cracked_stone_bricks', 'mossy_stone_bricks', 'andesite']) if y == 1 else 'white_terracotta'))
            cv.set(x, 4, z, 'spruce_log[axis=%s]' % ('x' if z in (Z0, Z1) and not corner else ('z' if not corner else 'y')))
    for z in (zc - 1, zc, zc + 1):                                      # the doorway
        for y in (1, 2, 3): cv.set(X1, y, z, None)
        cv.set(X1, 0, z, 'polished_andesite')
    for y in (2, 3):                                                    # windows
        for z in (Z0, Z1):
            for x in (X0 + 2, X0 + 3, X1 - 3, X1 - 2): cv.set(x, y, z, 'glass_pane')
        for z in (Z0 + 1, Z1 - 1): cv.set(X1, y, z, 'glass_pane')
    # --- the roof: a gable whose ridge runs east-west, overhanging one block all round
    for x in range(X0 - 1, X1 + 2):
        for i, z in enumerate(range(Z0 - 1, zc)):
            cv.set(x, 4 + i, z, 'dark_oak_stairs[facing=south,half=bottom]'); cv.set(x, 4 + i, 2 * zc - z, 'dark_oak_stairs[facing=north,half=bottom]')
        cv.set(x, 4 + (zc - Z0 + 1), zc, 'dark_oak_slab[type=bottom]')
    for x in (X0, X1):                                                  # gable walls
        for z in range(Z0 + 1, Z1):
            for y in range(5, 4 + (zc - Z0 + 1) - abs(z - zc)): cv.set(x, y, z, 'spruce_planks')
    ridge = 4 + (zc - Z0 + 1)
    # --- the front: sign in the gable, lanterns beside the door
    wall_sign(cv, X1 + 1, 5, zc, [('', 'black'), ('업그레이드', 'gold'), ('코인으로 해금', 'white')], facing='east')
    for z in (zc - 2, zc + 2): hang_lamp(cv, X1 + 1, 4, z, chain=2)
    cv.set(-10, 1, zc - 2, 'spruce_fence'); sign(cv, -10, 2, zc - 2, [('업그레이드', 'gold'), ('상점 물건 해금', 'white'), ('◀ 이쪽', 'aqua')], rotation=12)
    # --- inside: the counter from wall to wall, the keeper's shelves behind it, a small workshop in front
    cx = X0 + 4
    for z in range(Z0 + 1, Z1): cv.set(cx, 1, z, 'dark_oak_planks')
    cv.set(cx, 2, Z0 + 1, 'lantern[hanging=false]'); cv.set(cx, 2, Z1 - 1, 'lantern[hanging=false]')
    row1 = ['bookshelf', 'barrel[facing=east]', 'barrel[facing=east]', 'smithing_table', 'barrel[facing=east]', 'barrel[facing=east]', 'bookshelf']
    row2 = ['bookshelf', 'iron_block', 'gold_block', 'emerald_block', 'diamond_block', 'netherite_block', 'bookshelf']
    for i, z in enumerate(range(Z0 + 1, Z1)):
        cv.set(X0 + 1, 1, z, row1[i]); cv.set(X0 + 1, 2, z, row2[i]); cv.set(X0 + 1, 3, z, 'bookshelf')
    for x in range(cx + 1, X1):                                         # a runner from the door to the counter
        for z in (zc - 1, zc, zc + 1): cv.set(x, 1, z, 'yellow_carpet' if z == zc else 'orange_carpet')
    cv.set(X1 - 2, 1, Z0 + 1, 'anvil[facing=west]'); cv.set(X1 - 3, 1, Z0 + 1, 'smithing_table'); cv.set(X1 - 4, 1, Z0 + 1, 'barrel[facing=up]')
    cv.set(X1 - 2, 1, Z1 - 1, 'enchanting_table'); cv.set(X1 - 3, 1, Z1 - 1, 'bookshelf'); cv.set(X1 - 3, 2, Z1 - 1, 'bookshelf'); cv.set(X1 - 4, 1, Z1 - 1, 'bookshelf')
    for x in (X0 + 2, X1 - 3): hang_lamp(cv, x, ridge - 3, zc, chain=2)
    cv.marker(UNLOCK_NPC[0], UNLOCK_NPC[1], UNLOCK_NPC[2], ['bw', 'bw.lobby', 'bw.lobby.unlock'])
    counter(cv, cx, 1, zc, 1, 'east', ['bw', 'bw.lobby', 'bw.gui', 'bw.gui.unlock'])       # the unlock window (v8)

MARKET = dict(x0=-31, x1=-21, z0=-12, z1=2, floor=-8, hole=(-26, -5))     # the black market: a cellar under the giant bed
DEALER = (-26, -7, -10, 0.0)                                             # its keeper (lobby coordinates), looking south at the stairs

def black_market(cv):
    """Under the giant bed there is a hole in the lawn; a ladder leads down to a cellar where a dealer sells things no shop would.
    Nothing shows from outside: the hole is in the bed's shadow and the cellar is dug into the island."""
    import random
    rng = random.Random(9133)
    X0, X1, Z0, Z1, F = MARKET['x0'], MARKET['x1'], MARKET['z0'], MARKET['z1'], MARKET['floor']
    hx, hz = MARKET['hole']
    for x in range(X0 - 1, X1 + 2):                                   # the island must be thick enough to hide the room
        for z in range(Z0 - 1, Z1 + 2):
            assert all(cv.get(x, y, z) for y in range(F - 2, 0)), ('the cellar would show at', (x, z))
    wall = lambda: rng.choice(['polished_blackstone_bricks'] * 6 + ['cracked_polished_blackstone_bricks'] * 2 + ['polished_blackstone', 'deepslate_tiles'])
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            edge = x in (X0, X1) or z in (Z0, Z1)
            cv.set(x, F, z, 'deepslate_tiles' if (x + z) % 2 else 'polished_blackstone')
            for y in range(F + 1, F + 5): cv.set(x, y, z, wall() if edge else None)
            cv.set(x, F + 5, z, 'dark_oak_planks' if not edge else wall())
    for x in range(X0 + 1, X1):                                        # beams under the ceiling
        if (x - X0) % 3 == 0:
            for z in range(Z0 + 1, Z1): cv.set(x, F + 4, z, 'dark_oak_slab[type=top]')
    # the way in: a hole in the lawn under the bed, a ladder down the south wall of the shaft
    for y in range(F + 5, 1): cv.set(hx, y, hz, None)
    for y in range(F + 1, 1): cv.set(hx, y, hz, 'ladder[facing=north]')
    for y in range(F + 5, 0): cv.set(hx, y, hz + 1, wall())            # what the ladder hangs on, above the ceiling
    for y in (1, 2): assert cv.name(hx, y, hz) in (None,) + SOFT
    cv.set(hx, 1, hz, None)
    # the dealer's end: counter with the chest, shelves of contraband behind him
    dz = DEALER[2]
    for x in range(X0 + 1, X1): cv.set(x, F + 1, dz + 2, 'crying_obsidian' if x in (hx - 1, hx + 2) else 'polished_blackstone_wall')
    counter_ns(cv, hx, F + 1, dz + 2, ['bw', 'bw.lobby', 'bw.gui', 'bw.gui.black'])
    shelf = ['barrel[facing=south]', 'bookshelf', 'ender_chest[facing=south]', 'tnt', 'barrel[facing=south]', 'respawn_anchor[charges=2]', 'bookshelf', 'barrel[facing=south]', 'lodestone']
    for i, x in enumerate(range(X0 + 1, X1)):
        cv.set(x, F + 1, Z0 + 1, shelf[i % len(shelf)]); cv.set(x, F + 2, Z0 + 1, rng.choice(['bookshelf', 'barrel[facing=south]', 'chiseled_bookshelf[facing=south]']))
        cv.set(x, F + 3, Z0 + 1, 'polished_blackstone_slab[type=top]')
    for x in (X0 + 1, X1 - 1):
        cv.set(x, F + 3, dz + 2, 'soul_lantern[hanging=false]') if False else cv.set(x, F + 2, dz + 2, 'soul_lantern[hanging=false]')
    # the room: rugs, crates, a brewing corner, soul light
    for x in range(hx - 1, hx + 2):
        for z in range(dz + 3, Z1): cv.set(x, F + 1, z, 'purple_carpet' if x == hx else 'black_carpet')
    for y in range(F + 1, F + 5): cv.set(hx, y, hz + 1, 'dark_oak_log[axis=y]')           # the post the ladder hangs on
    cv.set(hx, F + 1, hz, 'ladder[facing=north]')
    for x, z in ((X0 + 1, Z1 - 1), (X0 + 1, Z1 - 2), (X0 + 2, Z1 - 1), (X1 - 1, Z1 - 1), (X1 - 1, Z1 - 3)): cv.set(x, F + 1, z, 'barrel[facing=up]')
    cv.set(X0 + 1, F + 2, Z1 - 1, 'barrel[facing=up]'); cv.set(X1 - 1, F + 2, Z1 - 1, 'skeleton_skull[rotation=6]')
    cv.set(X1 - 1, F + 1, hz - 1, 'brewing_stand'); cv.set(X1 - 1, F + 1, hz, 'cauldron'); cv.set(X1 - 1, F + 1, hz + 2, 'cobweb')
    cv.set(X0 + 1, F + 1, hz - 2, 'smithing_table'); cv.set(X0 + 1, F + 1, hz - 1, 'grindstone[face=floor,facing=east]'); cv.set(X0 + 1, F + 4, Z1 - 1, 'cobweb')
    for x, z in ((X0 + 2, hz + 3), (X1 - 2, hz + 3), (X0 + 2, dz + 4), (X1 - 2, dz + 4)):
        cv.set(x, F + 4, z, 'iron_chain[axis=y]'); cv.set(x, F + 3, z, 'soul_lantern[hanging=true]')
    wall_sign(cv, hx + 1, F + 3, Z1 - 1, [('암시장', 'dark_purple'), ('', 'black'), ('여기서 본 건', 'white'), ('비밀이야', 'white')], facing='north', wood='dark_oak')
    cv.marker(DEALER[0], DEALER[1], DEALER[2], ['bw', 'bw.lobby', 'bw.lobby.black'])

def counter_ns(cv, x, y, z, tags):
    """a double chest at (x, y, z) and (x + 1, y, z) looking south, with a marker on each half"""
    cv.set(x, y, z, 'waxed_copper_chest[facing=south,type=right]'); cv.set(x + 1, y, z, 'waxed_copper_chest[facing=south,type=left]')
    for xx in (x, x + 1): cv.marker(xx, y, z, tags)

def emblem(cv, mid, x, y, z):
    """a small model of the map standing on the wall above its gate"""
    if mid == 'tea':
        disc(cv, x, y, z, 3.4, 'white_concrete'); cyl(cv, x, y + 1, y + 3, z, 2.4, lambda a, b, c: 'white_concrete' if b == y + 2 else 'pink_concrete', hollow=True)
        disc(cv, x, y + 3, z, 1.6, 'orange_stained_glass'); cv.set(x + 3, y + 2, z, 'pink_concrete'); cv.set(x + 4, y + 2, z, 'pink_concrete') if False else None
        cv.set(x + 3, y + 3, z, 'pink_concrete'); cv.set(x + 3, y + 1, z, 'pink_concrete')
    elif mid == 'chess':
        chess_piece(cv, x - 2, y, z, 'king', 'smooth_quartz', f=0.75, trim='gold_block'); chess_piece(cv, x + 2, y, z, 'rook', 'polished_blackstone', f=0.75)
    elif mid == 'circus':
        m03_circus.mini_tent(cv, x, y, z, 3, 'red', 'white', door=(0, 1), n=8)
    elif mid == 'library':
        m06_library.book(cv, x - 3, z - 2, x + 3, z + 2, y, y + 1, 'red_terracotta', 'x0'); m06_library.book(cv, x - 2, z - 2, x + 3, z + 1, y + 2, y + 3, 'blue_terracotta', 'z0')
        m06_library.book(cv, x - 3, z - 1, x + 2, z + 2, y + 4, y + 5, 'green_terracotta', 'x1')
    elif mid == 'solar':
        sphere(cv, x, y + 4, z, 3.2, bands(['orange_terracotta', 'yellow_terracotta', 'orange_concrete', 'white_terracotta'], 1))
        for a in range(0, 360, 10):
            px, pz = x + round(5.4 * math.cos(math.radians(a))), z + round(5.4 * math.sin(math.radians(a)))
            cv.set(px, y + 4 + (1 if px > x + 2 else -1 if px < x - 2 else 0), pz, 'white_stained_glass')
        cv.set(x, y, z, 'iron_bars'); cv.set(x, y + 1, z, 'iron_bars') if False else cv.set(x, y, z, 'smooth_quartz')

def tower(cv, x, z, h=17, r=5.5):
    for y in range(1, h + 1):
        disc(cv, x, y, z, r if y < h - 1 else r + 1, WALL, r_in=(r if y < h - 1 else r + 1) - 1)
    disc(cv, x, h - 2, z, r, 'spruce_planks'); disc(cv, x, 0, z, r, PAVE)
    for a in range(0, 360, 45): cv.set(x + round((r + 1) * math.cos(math.radians(a))), h + 1, z + round((r + 1) * math.sin(math.radians(a))), 'stone_bricks')
    cone(cv, x, h + 1, z, r - 0.3, 8, 'deepslate_tiles'); cv.set(x, h + 9, z, 'lightning_rod[facing=up]')
    for y in range(1, h - 1): cv.set(x, y, z - int(r) + 1, 'ladder[facing=south]')
    cv.set(x, h - 2, z - int(r) + 1, 'ladder[facing=south]')
    for y in (1, 2, 3): cv.set(x, y, z + int(r), None)                    # door towards the lawn
    for y in (6, 7, 11, 12):
        for sx in (-1, 1): cv.set(x + sx * int(r), y, z, 'glass_pane')
    hang_lamp(cv, x + 2, h - 3, z); cv.set(x - 2, 1, z + 2, 'barrel[facing=up]'); cv.set(x + 2, 1, z + 2, 'barrel[facing=up]'); cv.set(x - 3, 1, z, 'crafting_table')
    cv.set(x + 2, h - 1, z + 1, 'lantern[hanging=false]'); cv.set(x - 2, h - 1, z + 1, 'barrel[facing=up]')

def balloon(dye):
    cv = Canvas(sum(map(ord, dye)) + 30)
    st = sectors(0, 0, 8, [dye + '_wool', 'white_wool'])
    ellipsoid(cv, 0, 12, 0, 6, 7, 6, st, hollow=True)
    for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)): cv.set(dx, 5, dz, None)
    box(cv, -1, -1, -1, 1, -1, 1, 'spruce_planks')
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if dx or dz: cv.set(dx, 0, dz, 'spruce_fence')
    for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        for y in range(1, 6): cv.set(dx, y, dz, 'iron_chain[axis=y]')
    cv.set(0, 4, 0, 'campfire[lit=true]') if False else cv.set(0, 0, 0, 'lantern[hanging=false]')
    return cv

def giant_bed(cv, x, y, z):
    """a bed big enough for a giant: 9 wide (x), 15 long (z), head towards -z"""
    for sx in (0, 8):
        for sz in (0, 14):
            for yy in range(y, y + 2): cv.set(x + sx, yy, z + sz, 'oak_log[axis=y]')
    box(cv, x, y + 2, z, x + 8, y + 2, z + 14, 'oak_planks'); box(cv, x, y + 3, z, x + 8, y + 3, z + 14, 'white_wool')
    box(cv, x, y + 4, z + 5, x + 8, y + 4, z + 14, 'red_wool'); box(cv, x, y + 3, z + 5, x, y + 3, z + 14, 'red_wool'); box(cv, x + 8, y + 3, z + 5, x + 8, y + 3, z + 14, 'red_wool')
    box(cv, x + 1, y + 4, z + 1, x + 7, y + 4, z + 3, 'white_wool'); box(cv, x, y + 3, z, x + 8, y + 6, z, 'oak_planks'); box(cv, x, y + 4, z + 4, x + 8, y + 4, z + 4, 'white_wool')

def build(maps, seed=77):
    """maps: list of dicts with id, name, size_text, gate (frame, roof_full, plaza, glass). Returns (canvas, pads, spawn)."""
    cv = Canvas(seed)
    hm = island(cv, 0, 0, -6, squircle(62, 56, 2.6), 34, TH, seed=11, flat=0.78, hill=2.6, rough=0.14, ext=(63, 57))
    flatten(cv, hm, -47, WZ0 - 2, 47, 32, 0, TH)
    # --- spawn plaza: the eight team colours as a compass, lamps, benches
    sx, sz = 0, 22
    def plaza(x, y, z):
        r = math.hypot(x - sx, z - sz)
        if r < 1.2: return 'sea_lantern'
        if r < 5.2: return DYES[int(((math.degrees(math.atan2(z - sz, x - sx)) + 360 + 22.5) % 360) / 45)] + '_concrete'
        if r < 6.2 or r >= 8.6: return 'smooth_quartz'
        return cv.pick(PAVE)
    disc(cv, sx, 0, sz, 9.4, plaza)
    for a in (35, 145, 215, 325):
        post_lamp(cv, sx + round(9 * math.cos(math.radians(a))), 1, sz + round(9 * math.sin(math.radians(a))), 'spruce_fence', 'lantern', 3)
    for dx in (-1, 0, 1):
        cv.set(sx + dx, 1, sz + 8, 'spruce_stairs[facing=south,half=bottom]')
        for s2 in (-1, 1): cv.set(sx + s2 * 8, 1, sz + dx, 'spruce_stairs[facing=%s,half=bottom]' % ('east' if s2 > 0 else 'west'))
    # --- avenue to the wall, cross path along the gates, team flags
    for z in range(WZ1 + 1, sz - 8):
        for x in range(-3, 4):
            if hm.get((x, z)) == 0: cv.set(x, 0, z, cv.pick(PAVE) if abs(x) < 3 else 'polished_andesite')
    for z in range(WZ1 + 1, WZ1 + 5):
        for x in range(-38, 39):
            if hm.get((x, z)) == 0: cv.set(x, 0, z, cv.pick(PAVE) if z < WZ1 + 4 else 'polished_andesite')
    for i, dye in enumerate(DYES):
        fx = -6 if i < 4 else 6; fz = 9 - (i % 4) * 7
        cv.set(fx, 0, fz, 'polished_andesite'); flag(cv, fx, 1, fz, 7, dye, d=(-1 if fx < 0 else 1, 0), pole='spruce_fence', w=3, hh=2)
    # --- the castle wall with five gates
    for x in range(-40, 41):
        for z in range(WZ0, WZ1 + 1):
            cv.set(x, 0, z, 'stone_bricks')
            for y in range(1, 10): cv.set(x, y, z, cv.pick(WALL))
        for z in (WZ0, WZ1):
            cv.set(x, 10, z, 'stone_bricks')
            if x % 2 == 0: cv.set(x, 11, z, 'stone_bricks')
        for y in (9,): cv.set(x, y, WZ1 + 1, 'stone_brick_stairs[facing=north,half=top]'); cv.set(x, y, WZ0 - 1, 'stone_brick_stairs[facing=south,half=top]')
    pads = []
    for i, (gx, mt) in enumerate(zip(GATE_X, maps)):
        g = mt['gate']; frame = g['frame']; cells = []
        for x in range(gx - 3, gx + 4):
            for z in range(WZ0 + 1, WZ1 + 1):                             # alcove, three deep; the back is a sheet of coloured glass
                edge = abs(x - gx) == 3
                for y in range(1, 8):
                    arch = y == 7 or (y == 6 and abs(x - gx) == 2)
                    if edge or arch: cv.set(x, y, z, frame)
                    elif z == WZ0 + 1: cv.set(x, y, z, g['glass'])
                    else: cv.set(x, y, z, None)
                if not edge and z > WZ0 + 1:
                    cv.set(x, 0, z, 'sea_lantern' if (x == gx and z == WZ0 + 3) else g['plaza']); cells.append((x, z))
            cv.set(x, 8, WZ1, g['roof_full']); cv.set(x, 8, WZ1 + 1, g['roof_full']) if abs(x - gx) <= 2 else None
        for s2 in (-1, 1):                                                # lamps on the piers, banner strip in the map's colours
            cv.set(gx + s2 * 3, 4, WZ1 + 1, 'spruce_fence') if False else None
            cv.set(gx + s2 * 4, 0, WZ1 + 2, 'polished_andesite'); post_lamp(cv, gx + s2 * 4, 1, WZ1 + 2, 'cobblestone_wall', 'lantern', 2) if s2 < 0 else None
        emblem(cv, mt['id'], gx, 11, WZ0 + 2)
        cv.set(gx + 4, 1, WZ1 + 2, 'spruce_fence')
        sign(cv, gx + 4, 2, WZ1 + 2, [(f"{i + 1}. {mt['name']}", 'gold'), (mt['size_text'], 'white'), ('8팀', 'white'), ('▶ 들어가기', 'aqua')], rotation=0)
        pads.append(dict(id=mt['id'], cells=cells))
    for tx in (-44, 44): tower(cv, tx, WZ0 + 2)
    for tx in (-39, 39):                                                  # doorways from the towers onto the wall walk
        for y in (10, 11): cv.set(tx, y, WZ0 + 2, None)
    # --- BED WARS, floating above the wall in front of the spawn
    title(cv, 24, -44, scale=2, gap=1, space=4)
    # --- lawns: a giant bed, a pond with a bridge, stalls, trees, flowers
    giant_bed(cv, -30, 1, -12)
    px, pz = 27, 2
    for x in range(px - 9, px + 10):
        for z in range(pz - 7, pz + 8):
            d = math.hypot((x - px) / 8.0, (z - pz) / 6.0) + (cv.noise.n2(x, z, 4.0) - 0.5) * 0.25
            if d < 1 and hm.get((x, z)) == 0:
                cv.set(x, 0, z, 'water'); cv.set(x, -1, z, cv.pick([('sand', 2), ('gravel', 1), ('clay', 1)]))
                if d < 0.55: cv.set(x, -1, z, 'water'); cv.set(x, -2, z, cv.pick([('sand', 2), ('gravel', 1)]))
            elif d < 1.25 and hm.get((x, z)) == 0 and cv.name(x, 0, z) != 'water': cv.set(x, 0, z, cv.pick([('sand', 2), ('grass_block', 2), ('coarse_dirt', 1)]))
    for x in range(px - 10, px + 11):
        for z in (pz - 1, pz, pz + 1):
            if cv.name(x, 0, z) == 'water' or cv.name(x, 1, z) is None and abs(x - px) <= 9 and cv.name(x, 0, z) in ('water',): pass
        if cv.name(x, 0, pz) == 'water' or cv.name(x, 0, pz - 1) == 'water' or cv.name(x, 0, pz + 1) == 'water':
            for z in (pz - 1, pz, pz + 1): cv.set(x, 1, z, 'spruce_slab[type=bottom]' if abs(z - pz) < 1 or True else None)
            for z in (pz - 2, pz + 2):
                if (x - px) % 3 == 0 and cv.empty(x, 1, z) and cv.name(x, 0, z) != 'water': pass
    stall(cv, -14, 1, 14, 0, 'white', 'red'); stall(cv, 14, 1, 14, 0, 'white', 'blue')
    cv.set(-14, 0, 14, 'polished_andesite'); cv.set(14, 0, 14, 'polished_andesite')
    rng = cv.rng
    spots = []
    for k in range(60):
        a = rng.uniform(0, 360); r = rng.uniform(0.6, 0.93)
        x, z = round(62 * r * math.cos(math.radians(a))), round(-6 + 56 * r * math.sin(math.radians(a)))
        if (x, z) not in hm or abs(x) < 9 and z > WZ1 or (abs(x) < 49 and WZ0 - 3 <= z <= WZ1 + 6) or math.hypot(x - sx, z - sz) < 13: continue
        if math.hypot(x - px, z - pz) < 12 or (-33 <= x <= -19 and -15 <= z <= 6): continue
        if any(math.hypot(x - a2, z - b2) < 6 for a2, b2 in spots): continue
        y = hm[(x, z)]
        if cv.name(x, y, z) not in ('grass_block', 'moss_block', 'podzol') or not cv.empty(x, y + 1, z): continue
        spots.append((x, z))
        if k % 5 == 0: oak(cv, x, y + 1, z, rng.randint(5, 7), 'birch_log', 'birch_leaves', 2.8, seed=k)
        elif k % 7 == 0: big_tree(cv, x, y + 1, z, rng.randint(8, 10), 'oak_log', 'oak_leaves', 4.6, seed=k)
        else: spruce(cv, x, y + 1, z, rng.randint(9, 15), 'spruce_log', 'spruce_leaves', 3)
    flora(cv, hm, [('short_grass', 10), ('fern', 4), ('poppy', 0.6), ('dandelion', 0.6), ('oxeye_daisy', 0.6), ('cornflower', 0.4), ('large_fern|tall', 1)], 0.14,
          on=('grass_block', 'moss_block', 'podzol'), avoid=lambda x, z: (abs(x) < 9 and z > WZ1) or math.hypot(x - sx, z - sz) < 11)
    # --- hot-air balloons beside the island
    cv.paste(balloon('red'), -74, 14, 8); cv.paste(balloon('blue'), 74, 20, -8); cv.paste(balloon('yellow'), -64, 30, 34); cv.paste(balloon('lime'), 62, 12, 42)
    cv.marker(sx, 1, sz, ['bw', 'bw.lobby', 'bw.lobby.spawn'])
    upgrade_hall(cv)
    black_market(cv)
    return cv, pads, (sx + 0.5, 1.0, sz + 0.5)

if __name__ == '__main__':
    import sys, check, preview
    maps = [dict(id=i, name=n, size_text='137x137', gate=g) for i, n, g in (
        ('tea', '티타임', dict(frame='smooth_quartz', roof_full='pink_concrete', plaza='white_concrete', glass='pink_stained_glass')),
        ('chess', '체스', dict(frame='polished_blackstone_bricks', roof_full='smooth_quartz', plaza='quartz_bricks', glass='white_stained_glass')),
        ('circus', '서커스', dict(frame='red_wool', roof_full='yellow_wool', plaza='birch_planks', glass='yellow_stained_glass')),
        ('library', '도서관', dict(frame='dark_oak_planks', roof_full='bookshelf', plaza='spruce_planks', glass='orange_stained_glass')),
        ('solar', '태양계', dict(frame='smooth_quartz', roof_full='black_concrete', plaza='light_gray_concrete', glass='light_blue_stained_glass')))]
    cv, pads, spawn = build(maps)
    check.states(cv, 'lobby'); ph = check.physics(cv, 'lobby', fix=False)
    (x0, y0, z0), (x1, y1, z1) = cv.bounds(); print('lobby size', x1 - x0 + 1, z1 - z0 + 1, 'y', y0, y1, 'blocks', len(cv.b), 'physics', sum(ph.values()), 'pads', [len(p['cells']) for p in pads])
    preview.fit(preview.side_by_side([preview.front(cv, 5, zmin=-40, zmax=40), preview.iso2(cv, 3, 0, 2.2)]), 1950, 1000).save(preview.os.path.join(check.ROOT, 'out3', 'preview', 'lobby_new.png'))

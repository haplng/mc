"""The ten map themes: palettes, base trees, houses, diamond-island and middle-island centerpieces."""
import math
import parts as PT
from parts import LEAF
import interior as IN

STONE = [('stone', 5), ('andesite', 3), ('tuff', 2), ('cobblestone', 1), ('gravel', 1), ('dirt', 1)]

def ring(cv, x, y, z, r, s, hollow=True):
    for dx in range(-r - 1, r + 2):
        for dz in range(-r - 1, r + 2):
            d = math.hypot(dx, dz)
            if (r - 0.5 <= d < r + 0.5) if hollow else d < r + 0.5:
                cv.set(x + dx, y, z + dz, s)

def disc(cv, x, y, z, r, s):
    ring(cv, x, y, z, r, s, hollow=False)

def pond(cv, hm, x, z, r, rim, depth=2, lily=None):
    """a water pond sunk into the island top, with a rim so the water cannot spill"""
    y = hm.get((x, z), 0)
    for dx in range(-r - 2, r + 3):
        for dz in range(-r - 2, r + 3):
            d = math.hypot(dx, dz)
            px, pz = x + dx, z + dz
            if d < r + 1.5 and (px, pz) in hm:
                for yy in range(y + 1, y + 4): cv.set(px, yy, pz, None)
            if d < r + 0.5:
                for yy in range(y - depth, y + 1): cv.set(px, yy, pz, 'water')
                cv.set(px, y - depth - 1, pz, cv.pick(rim))
                if lily and cv.rng.random() < 0.12: cv.set(px, y + 1, pz, lily)
            elif d < r + 1.5:
                for yy in range(y - depth - 1, y + 1): cv.set(px, yy, pz, cv.pick(rim))

def pillar(cv, x, y, z, h, s):
    for i in range(h): cv.set(x, y + i, z, s)

# ====================================================================== 1. cherry blossom garden
def sakura_tree(cv, x, y, z, seed): PT.cherry(cv, x, y, z, 4 + seed % 2, 3.4, seed)

def stone_lantern(cv, x, y, z):
    cv.set(x, y, z, 'stone_brick_wall'); cv.set(x, y + 1, z, 'stone_brick_wall')
    cv.set(x, y + 2, z, 'lantern[hanging=false]')
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)): cv.set(x + dx, y + 3, z + dz, 'stone_brick_slab[type=bottom]')
    cv.set(x, y + 3, z, 'stone_bricks')

def torii(cv, x, y, z, axis='x', w=3, h=5):
    for s in (-w, w):
        px, pz = (x + s, z) if axis == 'x' else (x, z + s)
        pillar(cv, px, y, pz, h, 'red_concrete')
    for s in range(-w - 1, w + 2):
        px, pz = (x + s, z) if axis == 'x' else (x, z + s)
        cv.set(px, y + h, pz, 'red_concrete' if abs(s) <= w else 'dark_oak_slab[type=bottom]')
        cv.set(px, y + h + 1, pz, 'dark_oak_slab[type=bottom]')
        if abs(s) < w: cv.set(px, y + h - 2, pz, 'dark_oak_fence' if abs(s) != 0 else 'red_concrete')

def pagoda(cv, x, y, z, floors=3, w=5):
    yy = y
    for f in range(floors):
        r = w - f
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                cv.set(x + dx, yy, z + dz, 'dark_oak_planks')
                edge = max(abs(dx), abs(dz)) == r
                for hh in range(1, 4):
                    if edge:
                        corner = abs(dx) == r and abs(dz) == r
                        s = 'dark_oak_log' if corner else ('white_concrete' if hh < 3 else 'cherry_planks')
                        if not corner and hh == 2 and (abs(dx) + abs(dz)) % 2 == 0: s = 'cherry_trapdoor[facing=north,half=bottom,open=true]' if False else 'glass_pane'
                        cv.set(x + dx, yy + hh, z + dz, s)
                    else:
                        cv.set(x + dx, yy + hh, z + dz, None)
        # doors on all four sides on the ground floor
        if f == 0:
            for dx, dz in ((r, 0), (-r, 0), (0, r), (0, -r)):
                for hh in (1, 2): cv.set(x + dx, yy + hh, z + dz, None)
        # flared roof
        rr = r + 2; ry = yy + 4
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                m = max(abs(dx), abs(dz))
                if m == rr:
                    fa = 'south' if dz == -rr else 'north' if dz == rr else 'east' if dx == -rr else 'west'
                    cv.set(x + dx, ry, z + dz, f'deepslate_tile_stairs[facing={fa},half=bottom]')
                    if abs(dx) == rr and abs(dz) == rr: cv.set(x + dx, ry + 1, z + dz, 'deepslate_tile_slab[type=bottom]')
                elif m == rr - 1:
                    cv.set(x + dx, ry, z + dz, 'deepslate_tiles')
                else:
                    cv.set(x + dx, ry, z + dz, 'dark_oak_planks')
        cv.set(x, yy + 3, z, 'lantern[hanging=true]')
        yy = ry
    pillar(cv, x, yy + 1, z, 3, 'dark_oak_fence'); cv.set(x, yy + 4, z, 'lightning_rod[facing=up]')
    for i in range(1, 4): cv.set(x, yy + i, z, 'iron_chain[axis=y]' if i == 3 else 'dark_oak_fence')
    return yy

def sakura_mid(cv, hm, seed, Rm, em):
    pagoda(cv, 0, 1, 0, 3, 5)
    for x in range(-6, 7):
        for z in range(-6, 7): cv.set(x, 0, z, cv.pick([('stone_bricks', 3), ('mossy_stone_bricks', 1)]))
    for i, (ex, ez) in enumerate(em):
        tx, tz = ex * 0.62, ez * 0.62
        torii(cv, round(tx), 1, round(tz), 'z' if ex else 'x', 2, 4)
        for t in range(7, int(math.hypot(ex, ez)) - 2):
            px, pz = round(ex / max(1, abs(ex) or abs(ez)) * t) if ex else 0, round(ez / max(1, abs(ez)) * t) if ez else 0
            cv.set(px, 0, pz, cv.pick([('gravel', 2), ('stone_bricks', 1)]))
    pond(cv, hm, round(Rm * 0.55), round(Rm * 0.55), 3, [('stone', 2), ('mossy_cobblestone', 1)], 2, 'lily_pad')
    for k in range(4):
        a = math.radians(45 + 90 * k + 18)
        x, z = round(Rm * 0.7 * math.cos(a)), round(Rm * 0.7 * math.sin(a))
        if (x, z) in hm: PT.cherry(cv, x, hm[(x, z)] + 1, z, 5, 4.2, seed + k)
    for k in range(4):
        a = math.radians(90 * k + 45)
        x, z = round(8.5 * math.cos(a)), round(8.5 * math.sin(a))
        stone_lantern(cv, x, 1, z)

def sakura_dia(cv, hm, seed):
    stone_lantern(cv, 4, 1, -3)
    for i in range(6):
        x, z = -4 + i % 2, 3 + i // 2
        if (x, z) in hm:
            for h in range(4 + i % 3): cv.set(x, hm[(x, z)] + 1 + h, z, 'bamboo[age=0,leaves=' + ('large' if h >= 3 else 'none') + ',stage=0]')
    PT.cherry(cv, -4, hm.get((-4, -4), 0) + 1, -4, 4, 2.8, seed)

# ====================================================================== 2. desert oasis
def desert_house(cv, th, dye, x0=-5, x1=5, z0=-14, z1=-8, h=4):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            cv.set(x, 0, z, 'smooth_sandstone')
            for y in range(1, h + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                cv.set(x, y, z, ('cut_sandstone' if y == h else 'smooth_sandstone') if edge else None)
            cv.set(x, h + 1, z, 'smooth_sandstone_slab[type=bottom]' if x not in (x0, x1) and z not in (z0, z1) else 'sandstone_wall')
    for x in range(x0, x1 + 1, 2):
        for z in (z0, z1): cv.set(x, h + 2, z, 'sandstone_wall')
    mid = (x0 + x1) // 2
    for y in (1, 2): cv.set(mid, y, z1, None)
    cv.set(mid, 3, z1, 'chiseled_sandstone')
    # striped team awning over the door
    for x in range(mid - 3, mid + 4):
        cv.set(x, 3, z1 + 1, f'{dye}_wool' if (x - mid) % 2 == 0 else 'white_wool')
        cv.set(x, 2, z1 + 2, f'{dye}_carpet' if False else None)
    cv.set(mid - 3, 1, z1 + 1, 'sandstone_wall'); cv.set(mid - 3, 2, z1 + 1, 'sandstone_wall')
    cv.set(mid + 3, 1, z1 + 1, 'sandstone_wall'); cv.set(mid + 3, 2, z1 + 1, 'sandstone_wall')
    for x in (x0 + 2, x1 - 2): cv.set(x, 2, z1, 'orange_stained_glass_pane')
    # small dome on top
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if dx * dx + dz * dz <= 5: cv.set(mid + dx, h + 1, (z0 + z1) // 2 + dz, f'{dye}_terracotta')
            if dx * dx + dz * dz <= 2: cv.set(mid + dx, h + 2, (z0 + z1) // 2 + dz, f'{dye}_terracotta')
    cv.set(mid, h + 3, (z0 + z1) // 2, 'gold_block')
    IN.room(cv, x0 + 1, x1 - 1, z0 + 1, z1 - 1, 1, dye, 'desert', 'jungle', 'desert', door=(mid, z1 - 1), h=h - 1)
    cv.set(mid, h, (z0 + z1) // 2, 'lantern[hanging=true]')

def palm_tree(cv, x, y, z, seed):
    PT.palm(cv, x, y, z, 6 + seed % 3, [(1, 0), (0, 1), (-1, 0), (0, -1)][seed % 4], seed)

def oasis_mid(cv, hm, seed, Rm, em):
    # stepped pyramid
    w = int(Rm * 0.38) + 1; y = 1; lvl = 0
    while w >= 0:
        for dx in range(-w, w + 1):
            for dz in range(-w, w + 1):
                edge = max(abs(dx), abs(dz)) == w
                s = 'cut_sandstone' if lvl % 3 == 2 and edge else ('chiseled_sandstone' if edge and (dx == 0 or dz == 0) and lvl % 3 == 0 else 'sandstone')
                cv.set(dx, y, dz, s)
        w -= 1; y += 1; lvl += 1
    cv.set(0, y, 0, 'gold_block'); cv.set(0, y + 1, 0, 'lightning_rod[facing=up]')
    # entrance stairs on four sides
    W = int(Rm * 0.38) + 1
    for k, (fx, fz, fa) in enumerate(((1, 0, 'west'), (-1, 0, 'east'), (0, 1, 'north'), (0, -1, 'south'))):
        for i in range(W + 1):
            for s in (-1, 0, 1):
                px = fx * (W - i) + (s if fz else 0); pz = fz * (W - i) + (s if fx else 0)
                cv.set(px, 1 + i, pz, f'sandstone_stairs[facing={fa},half=bottom]')
    # obelisks on the diagonals
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, z = round(Rm * 0.62 * math.cos(a)), round(Rm * 0.62 * math.sin(a))
        pillar(cv, x, 1, z, 7, 'cut_sandstone'); cv.set(x, 8, z, 'chiseled_sandstone'); cv.set(x, 9, z, 'gold_block')
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)): cv.set(x + dx, 1, z + dz, 'sandstone_stairs[facing=%s,half=bottom]' % {(1, 0): 'west', (-1, 0): 'east', (0, 1): 'north', (0, -1): 'south'}[(dx, dz)])
    # oasis pools with palms between the gens
    for k in range(4):
        a = math.radians(90 * k + 45)
        x, z = round(Rm * 0.82 * math.cos(a)), round(Rm * 0.82 * math.sin(a))
        if (x, z) in hm:
            PT.palm(cv, x + 2, hm.get((x + 2, z), 0) + 1, z, 7, (1 if x > 0 else -1, 0), seed + k)

def oasis_dia(cv, hm, seed):
    for (x, z, h) in ((-4, 3, 3), (4, -3, 2), (-3, -4, 2)):
        if (x, z) in hm:
            for i in range(h): cv.set(x, hm[(x, z)] + 1 + i, z, 'cactus[age=0]')
    PT.palm(cv, 3, hm.get((3, 4), 0) + 1, 4, 6, (1, 0), seed)
    for x, z in ((5, 1), (5, 2)):
        if (x, z) in hm: cv.set(x, hm[(x, z)] + 1, z, 'cut_sandstone'); cv.set(x, hm[(x, z)] + 2, z, 'sandstone_slab[type=bottom]')

# ====================================================================== 3. frozen village
def spruce_snow(cv, x, y, z, seed): PT.spruce(cv, x, y, z, 8 + seed % 3, 'spruce_log', 'spruce_leaves', 3, snow=True)

def snow_roof(cv):
    for (x, y, z), s in list(cv.b.items()):
        if 'stairs' in s and 'spruce' in s and cv.empty(x, y + 1, z) and cv.rng.random() < 0.7:
            cv.set(x, y + 1, z, 'snow[layers=1]')

def cabin(cv, th, dye):
    from bwmap import cottage
    cottage(cv, th, dye)
    snow_roof(cv)

def ice_spike(cv, x, y, z, h, w=1):
    for i in range(h):
        r = max(0, round(w * (1 - i / h)))
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) + abs(dz) <= r: cv.set(x + dx, y + i, z + dz, 'packed_ice' if (i + dx) % 4 else 'blue_ice')

def frost_mid(cv, hm, seed, Rm, em):
    # round ice keep with battlements and a pointed roof
    R = max(4, int(Rm * 0.3)); H = 10
    for y in range(1, H + 1):
        ring(cv, 0, y, 0, R, 'packed_ice' if y % 4 else 'blue_ice')
    disc(cv, 0, 0, 0, R, 'polished_diorite')
    for dx, dz in ((R, 0), (-R, 0), (0, R), (0, -R)):
        for y in (1, 2, 3): cv.set(dx, y, dz, None)
        cv.set(dx, 4, dz, 'blue_ice')
    for y in range(4, H, 3):
        for dx, dz in ((R, 2), (-R, -2), (2, -R), (-2, R)): cv.set(dx, y, dz, 'light_blue_stained_glass')
    disc(cv, 0, H, 0, R, 'snow_block')
    for i, (dx, dz) in enumerate([(round(R * math.cos(a)), round(R * math.sin(a))) for a in [k * math.pi / 6 for k in range(12)]]):
        if i % 2 == 0: cv.set(dx, H + 1, dz, 'snow_block')
    for i in range(R + 4):
        r = max(0, R - 1 - i // 2)
        ring(cv, 0, H + 1 + i, 0, r, 'light_blue_concrete' if i % 2 == 0 else 'white_concrete', hollow=False) if r > 0 else cv.set(0, H + 1 + i, 0, 'light_blue_concrete')
    cv.set(0, 4, 0, 'sea_lantern')
    # ice spikes and snowy firs around
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, z = round(Rm * 0.55 * math.cos(a)), round(Rm * 0.55 * math.sin(a))
        ice_spike(cv, x, 1, z, 7 + k % 3, 1)
        x2, z2 = round(Rm * 0.8 * math.cos(a + 0.35)), round(Rm * 0.8 * math.sin(a + 0.35))
        if (x2, z2) in hm: PT.spruce(cv, x2, hm[(x2, z2)] + 1, z2, 9, snow=True)
    # frozen paths
    for ex, ez in em:
        for t in range(R + 1, int(math.hypot(ex, ez)) - 2):
            sx = (ex > 0) - (ex < 0); sz = (ez > 0) - (ez < 0)
            for s in (-1, 0, 1):
                cv.set(sx * t + (s if sz else 0), 0, sz * t + (s if sx else 0), 'blue_ice' if s == 0 else 'packed_ice')

def frost_dia(cv, hm, seed):
    ice_spike(cv, -4, 1, 3, 6, 1); ice_spike(cv, 4, 1, -3, 4, 1); ice_spike(cv, 3, 1, 4, 3, 0)
    PT.spruce(cv, -4, hm.get((-4, -4), 0) + 1, -4, 7, snow=True)

# ====================================================================== 4. giant mushrooms
def mush_tree(cv, x, y, z, seed): PT.mushroom(cv, x, y, z, 5 + seed % 3, 3, 'red' if seed % 2 else 'brown')

def mush_house(cv, th, dye, cz=-11):
    R = 4; H = 4
    for y in range(0, H + 1):
        ring(cv, 0, y, cz, R, 'mushroom_stem' if y else 'mushroom_stem', hollow=(y > 0))
    disc(cv, 0, 0, cz, R - 1, 'spruce_planks')
    for y in (1, 2): cv.set(0, y, cz + R, None)
    cv.set(0, 3, cz + R + 1, f'{dye}_wall_banner[facing=south]')
    for y in (2,):
        for dx, dz in ((R, 0), (-R, 0), (0, -R)): cv.set(dx, y, cz + dz, f'{dye}_stained_glass')
    # red cap with white (team) spots
    for i in range(4):
        r = R + 2 - i
        ring(cv, 0, H + 1 + i, cz, r, 'red_mushroom_block', hollow=(i < 3))
    for dx, dz, dy in ((2, 3, 2), (-3, 1, 1), (1, -3, 2), (-1, 4, 0), (3, -2, 1)):
        cv.set(dx, H + 1 + dy, cz + dz, f'{dye}_concrete')
    cv.set(0, H, cz, 'shroomlight')
    IN.round_room(cv, 0, cz, R - 1, 1, dye, 'mush', 'mush', door_dir=(0, 1))

def mush_mid(cv, hm, seed, Rm, em):
    PT.mushroom(cv, 0, 1, 0, 13, 8, 'red')
    for dx in range(-6, 7):
        for dz in range(-6, 7):
            if dx * dx + dz * dz < 30 and cv.get(dx, 13, dz) == 'minecraft:red_mushroom_block' and (dx + dz) % 3 == 0:
                cv.set(dx, 12, dz, 'shroomlight')
    for k in range(6):
        a = math.radians(30 + 60 * k)
        x, z = round(Rm * 0.7 * math.cos(a)), round(Rm * 0.7 * math.sin(a))
        if (x, z) in hm: PT.mushroom(cv, x, hm[(x, z)] + 1, z, 6 + k % 3, 3, 'brown' if k % 2 else 'red')
    ring(cv, 0, 0, 0, 3, 'moss_block', hollow=False)
    for k in range(8):
        a = k * math.pi / 4; x, z = round(4 * math.cos(a)), round(4 * math.sin(a))
        cv.set(x, 1, z, 'red_mushroom' if k % 2 else 'brown_mushroom')

def mush_dia(cv, hm, seed):
    PT.mushroom(cv, -4, hm.get((-4, 3), 0) + 1, 3, 5, 2, 'red')
    PT.mushroom(cv, 4, hm.get((4, -3), 0) + 1, -3, 4, 2, 'brown')
    cv.set(3, hm.get((3, 4), 0) + 1, 4, 'shroomlight')

# ====================================================================== 5. lighthouse harbour
def beach_tree(cv, x, y, z, seed):
    if seed % 2: PT.palm(cv, x, y, z, 6, [(1, 0), (0, 1), (-1, 0), (0, -1)][seed % 4], seed)
    else: PT.oak(cv, x, y, z, 5, 'oak_log', 'oak_leaves', 2.6, seed)

def lighthouse(cv, x, y, z, H=18, R=3):
    for i in range(H):
        ring(cv, x, y + i, z, R if i < H - 4 else R - 1, 'red_concrete' if (i // 3) % 2 else 'white_concrete', hollow=False)
    for dx, dz in ((R, 0),):
        for i in (1, 2): cv.set(x + dx, y + i, z + dz, None)
    top = y + H
    disc(cv, x, top, z, R + 1, 'spruce_planks'); ring(cv, x, top + 1, z, R + 1, 'spruce_fence')
    ring(cv, x, top + 1, z, R - 1, 'light_blue_stained_glass'); ring(cv, x, top + 2, z, R - 1, 'light_blue_stained_glass')
    disc(cv, x, top + 1, z, R - 2, 'sea_lantern'); cv.set(x, top + 2, z, 'sea_lantern')
    for i in range(4):
        r = R - 1 - i
        if r < 0: break
        disc(cv, x, top + 3 + i, z, r, 'red_concrete') if r > 0 else cv.set(x, top + 3 + i, z, 'red_concrete')
    cv.set(x, top + 3 + R, z, 'lightning_rod[facing=up]')

def harbour_mid(cv, hm, seed, Rm, em):
    lighthouse(cv, 0, 1, 0, 16 + Rm // 6, 3)
    # plank boardwalk ring with posts
    ring(cv, 0, 0, 0, int(Rm * 0.42), 'spruce_planks'); ring(cv, 0, 0, 0, int(Rm * 0.42) - 1, 'spruce_planks')
    for k in range(12):
        a = k * math.pi / 6; r = int(Rm * 0.42) + 1
        x, z = round(r * math.cos(a)), round(r * math.sin(a))
        if k % 3: PT.lantern_post(cv, x, 1, z, 'spruce_fence', 'lantern', 2)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, z = round(Rm * 0.66 * math.cos(a)), round(Rm * 0.66 * math.sin(a))
        if (x, z) in hm:
            pond(cv, hm, x, z, 3, [('sand', 2), ('stone', 1)], 2, 'lily_pad')
            for dx, dz in ((4, 0), (0, 4)):
                if (x + dx, z + dz) in hm: cv.set(x + dx, hm[(x + dx, z + dz)] + 1, z + dz, 'barrel[facing=up,open=false]')
        x2, z2 = round(Rm * 0.86 * math.cos(a + 0.4)), round(Rm * 0.86 * math.sin(a + 0.4))
        if (x2, z2) in hm: PT.palm(cv, x2, hm[(x2, z2)] + 1, z2, 7, (1 if x2 > 0 else -1, 0), seed + k)

def harbour_dia(cv, hm, seed):
    for (x, z) in ((-4, 2), (-4, 3), (-3, 3), (4, -3)):
        if (x, z) in hm: cv.set(x, hm[(x, z)] + 1, z, 'barrel[facing=up,open=false]')
    cv.set(-4, hm.get((-4, 3), 0) + 2, 3, 'barrel[facing=up,open=false]')
    PT.lantern_post(cv, 4, hm.get((4, 3), 0) + 1, 3, 'spruce_fence', 'lantern', 3)
    PT.palm(cv, 3, hm.get((3, -4), 0) + 1, -4, 6, (1, 0), seed)

# ====================================================================== 6. autumn farm
def fall_tree(cv, x, y, z, seed): PT.autumn_tree(cv, x, y, z, 5 + seed % 2, 3.2, seed)

def windmill(cv, x, y, z, H=12):
    for i in range(H):
        r = 4 if i < 3 else 3 if i < 8 else 2
        ring(cv, x, y + i, z, r, 'cobblestone' if i < 3 else 'spruce_planks' if i % 4 else 'stripped_spruce_wood', hollow=True)
    disc(cv, x, y, z, 3, 'spruce_planks')
    for i in (1, 2): cv.set(x + 4, y + i, z, None)
    for i in range(5):
        disc(cv, x, y + H + i, z, max(0, 3 - i), 'dark_oak_planks') if 3 - i > 0 else cv.set(x, y + H + i, z, 'dark_oak_planks')
    # the sails, facing +x
    hub = (x + 4, y + H - 2, z)
    cv.set(*hub, 'dark_oak_log[axis=x]')
    for dy, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for t in range(1, 8):
            px, py, pz = hub[0], hub[1] + dy * t, hub[2] + dz * t
            cv.set(px, py, pz, 'spruce_fence')
            sx = (0, 1) if dy else (1, 0)
            if t > 1:
                cv.set(px, py + (dz if dz else 0) * 0, pz + (1 if dy else 0), 'white_wool' if t % 2 else 'white_wool')
                cv.set(px, py + (1 if dz else 0), pz + (0), 'white_wool') if dz else None

def farm_mid(cv, hm, seed, Rm, em):
    windmill(cv, 0, 1, 0, 11 + Rm // 8)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x0, z0 = round(Rm * 0.6 * math.cos(a)), round(Rm * 0.6 * math.sin(a))
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                p = (x0 + dx, z0 + dz)
                if p in hm:
                    y = hm[p]; cv.set(p[0], y, p[1], 'farmland[moisture=7]' if (dx + dz) % 2 else 'farmland[moisture=7]')
                    cv.set(p[0], y + 1, p[1], 'pumpkin' if cv.rng.random() < 0.25 else 'wheat[age=7]' if k % 2 else 'carrots[age=7]')
        x1, z1 = round(Rm * 0.85 * math.cos(a + 0.4)), round(Rm * 0.85 * math.sin(a + 0.4))
        if (x1, z1) in hm: PT.autumn_tree(cv, x1, hm[(x1, z1)] + 1, z1, 6, 3.6, seed + k)
        x2, z2 = round(Rm * 0.45 * math.cos(a - 0.5)), round(Rm * 0.45 * math.sin(a - 0.5))
        if (x2, z2) in hm:
            cv.set(x2, hm[(x2, z2)] + 1, z2, 'hay_block[axis=y]'); cv.set(x2 + 1, hm[(x2, z2)] + 1, z2, 'hay_block[axis=x]')
            cv.set(x2, hm[(x2, z2)] + 2, z2, 'hay_block[axis=z]')

def farm_dia(cv, hm, seed):
    for (x, z, s) in ((-4, 3, 'pumpkin'), (-3, 4, 'carved_pumpkin[facing=south]'), (4, -3, 'hay_block[axis=y]'), (4, -2, 'hay_block[axis=x]')):
        if (x, z) in hm: cv.set(x, hm[(x, z)] + 1, z, s)
    PT.autumn_tree(cv, 3, hm.get((3, 4), 0) + 1, 4, 5, 2.8, seed)

def barn(cv, th, dye):
    from bwmap import cottage
    cottage(cv, th, dye)

# ====================================================================== 7. nether fortress
def fungus(cv, x, y, z, seed, h=None):
    kind = 'crimson' if seed % 2 else 'warped'
    h = h or 6 + seed % 3
    for i in range(h): cv.set(x, y + i, z, f'{kind}_stem[axis=y]')
    hat = 'nether_wart_block' if kind == 'crimson' else 'warped_wart_block'
    for dy in range(0, 3):
        r = 3 - dy
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) + abs(dz) <= r + 1:
                    cv.set(x + dx, y + h - 1 + dy, z + dz, 'shroomlight' if cv.rng.random() < 0.08 else hat)
    for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        if kind == 'crimson':
            for i in range(cv.rng.randint(1, 3)): cv.set(x + dx, y + h - 2 - i, z + dz, 'weeping_vines_plant' if i < 2 else 'weeping_vines[age=0]')

def nether_tower(cv, x, y, z, H, w=2):
    for i in range(H):
        for dx in range(-w, w + 1):
            for dz in range(-w, w + 1):
                if max(abs(dx), abs(dz)) == w: cv.set(x + dx, y + i, z + dz, 'nether_bricks' if i % 5 else 'red_nether_bricks')
    for dx in range(-w - 1, w + 2):
        for dz in range(-w - 1, w + 2):
            if max(abs(dx), abs(dz)) == w + 1 and (dx + dz) % 2 == 0: cv.set(x + dx, y + H, z + dz, 'nether_brick_fence')
            elif max(abs(dx), abs(dz)) <= w + 1: cv.set(x + dx, y + H - 1, z + dz, 'nether_bricks')
    cv.set(x, y + H, z, 'soul_soil' if False else 'netherrack'); cv.set(x, y + H + 1, z, 'fire')

def nether_mid(cv, hm, seed, Rm, em):
    # lava pool in a blackstone basin, four towers, arches toward the gens
    for dx in range(-5, 6):
        for dz in range(-5, 6):
            d = math.hypot(dx, dz)
            if d < 3.5:
                cv.set(dx, 0, dz, 'lava'); cv.set(dx, -1, dz, 'blackstone'); cv.set(dx, -2, dz, 'blackstone')
            elif d < 5: cv.set(dx, 0, dz, 'polished_blackstone_bricks'); cv.set(dx, 1, dz, 'polished_blackstone_brick_wall' if d >= 4.5 else None)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, z = round(Rm * 0.42 * math.cos(a)), round(Rm * 0.42 * math.sin(a))
        nether_tower(cv, x, 1, z, 11 + k % 2 * 2, 2)
    # arches between the towers
    for (ax, az, bx, bz) in ((1, 1, 1, -1), (1, -1, -1, -1), (-1, -1, -1, 1), (-1, 1, 1, 1)):
        r = Rm * 0.42 / math.sqrt(2)
        x0, z0, x1, z1 = round(ax * r * math.sqrt(2) * 0.71), round(az * r * math.sqrt(2) * 0.71), round(bx * r * math.sqrt(2) * 0.71), round(bz * r * math.sqrt(2) * 0.71)
        PT.trunk_line(cv, x0, 9, z0, x1, 9, z1, 'nether_bricks')
        PT.trunk_line(cv, x0, 10, z0, x1, 10, z1, 'nether_brick_fence')
    for k in range(6):
        a = math.radians(15 + 60 * k)
        x, z = round(Rm * 0.8 * math.cos(a)), round(Rm * 0.8 * math.sin(a))
        if (x, z) in hm: fungus(cv, x, hm[(x, z)] + 1, z, seed + k, 7 + k % 3)
    for ex, ez in em:
        cv.set(ex + (2 if ex > 0 else -2 if ex < 0 else 0), 1, ez + (2 if ez > 0 else -2 if ez < 0 else 0), 'soul_lantern[hanging=false]')

def nether_dia(cv, hm, seed):
    fungus(cv, -4, hm.get((-4, 3), 0) + 1, 3, seed, 6)
    for (x, z) in ((4, -3), (4, -2), (3, -3)):
        if (x, z) in hm: cv.set(x, hm[(x, z)] + 1, z, 'glowstone')
    cv.set(4, hm.get((4, -3), 0) + 2, -3, 'glowstone')

# ====================================================================== 8. jungle temple
def jungle_tree(cv, x, y, z, seed):
    PT.oak(cv, x, y, z, 6 + seed % 3, 'jungle_log', 'jungle_leaves', 3.0, seed)
    for dx, dz, fa in ((1, 0, 'west'), (-1, 0, 'east')):
        for i in range(2, 5): cv.set(x + dx, y + i, z + dz, f'vine[{fa}=true]'.replace('[west=true]', '[west=true]'))

def temple(cv, x, y, z, w, steps):
    yy = y
    for s in range(steps):
        r = w - s * 2
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                for h in range(2):
                    edge = max(abs(dx), abs(dz)) >= r - 1
                    if edge or h == 0:
                        cv.set(x + dx, yy + h, z + dz, cv.pick([('mossy_stone_bricks', 3), ('stone_bricks', 2), ('cracked_stone_bricks', 1), ('mossy_cobblestone', 1)]))
                    else:
                        cv.set(x + dx, yy + h, z + dz, None)
            # stairs up the middle of each side
        for k, (fx, fz, fa) in enumerate(((1, 0, 'west'), (-1, 0, 'east'), (0, 1, 'north'), (0, -1, 'south'))):
            for t in range(2):
                for sd in (-1, 0, 1):
                    px = x + fx * (r + 1 - t) + (sd if fz else 0); pz = z + fz * (r + 1 - t) + (sd if fx else 0)
                    cv.set(px, yy + t, pz, f'mossy_stone_brick_stairs[facing={fa},half=bottom]')
        yy += 2
    # shrine on top
    r = max(2, w - steps * 2)
    for dx, dz in ((r, r), (-r, r), (r, -r), (-r, -r)):
        pillar(cv, x + dx, yy, z + dz, 4, 'chiseled_stone_bricks')
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1): cv.set(x + dx, yy + 4, z + dz, 'mossy_stone_brick_slab[type=bottom]')
    cv.set(x, yy, z, 'gold_block'); cv.set(x, yy + 3, z, 'lantern[hanging=true]')
    return yy

def jungle_mid(cv, hm, seed, Rm, em):
    temple(cv, 0, 1, 0, int(Rm * 0.36), 3)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, z = round(Rm * 0.72 * math.cos(a)), round(Rm * 0.72 * math.sin(a))
        if (x, z) in hm: PT.big_oak(cv, x, hm[(x, z)] + 1, z, 9, 'jungle_log', 'jungle_leaves', 5.0, seed + k)
    for (x, y, z), s in list(cv.b.items()):
        if ('stone_bricks' in s or 'cobblestone' in s) and y > 1 and cv.rng.random() < 0.08:
            for dx, dz, fa in ((1, 0, 'west'), (-1, 0, 'east'), (0, 1, 'north'), (0, -1, 'south')):
                if cv.empty(x + dx, y, z + dz):
                    for i in range(cv.rng.randint(1, 3)):
                        if cv.empty(x + dx, y - i, z + dz): cv.set(x + dx, y - i, z + dz, f'vine[{fa}=true]')
                    break

def jungle_dia(cv, hm, seed):
    for (x, z, h) in ((-4, 3, 4), (-4, -3, 2), (4, 3, 3)):
        if (x, z) in hm:
            pillar(cv, x, hm[(x, z)] + 1, z, h, 'mossy_stone_bricks'); cv.set(x, hm[(x, z)] + 1 + h, z, 'mossy_stone_brick_slab[type=bottom]')
    jungle_tree(cv, 4, hm.get((4, -4), 0) + 1, -4, seed)

# ====================================================================== 9. sky castle
def birch_tree(cv, x, y, z, seed): PT.oak(cv, x, y, z, 6 + seed % 2, 'birch_log', 'birch_leaves', 2.5, seed)

def castle_tower(cv, x, y, z, H, r, roof, wall='quartz_bricks'):
    for i in range(H):
        ring(cv, x, y + i, z, r, wall if i % 5 else 'chiseled_quartz_block')
    disc(cv, x, y + H, z, r + 1, 'smooth_quartz')
    for i in range(r + 4):
        rr = r + 1 - i
        if rr <= 0:
            cv.set(x, y + H + 1 + i, z, roof); cv.set(x, y + H + 2 + i, z, 'gold_block'); cv.set(x, y + H + 3 + i, z, 'lightning_rod[facing=up]'); break
        ring(cv, x, y + H + 1 + i, z, rr, roof, hollow=False)
    for dx, dz in ((r, 0), (-r, 0), (0, r), (0, -r)):
        cv.set(x + dx, y + H - 3, z + dz, 'light_blue_stained_glass')

def tower_house(cv, th, dye):
    castle_tower(cv, 0, 0, -11, 7, 3, f'{dye}_concrete')
    for y in (1, 2): cv.set(0, y, -8, None)
    cv.set(0, 3, -7, f'{dye}_wall_banner[facing=south]')
    disc(cv, 0, 0, -11, 2, 'smooth_quartz')
    for dx, dz in ((-5, -9), (5, -9)):
        castle_tower(cv, dx, 0, dz, 4, 1, f'{dye}_concrete')
    IN.round_room(cv, 0, -11, 2, 1, dye, 'castle', 'castle', door_dir=(0, 1))
    cv.set(0, 6, -11, 'lantern[hanging=true]')

def castle_mid(cv, hm, seed, Rm, em):
    w = int(Rm * 0.32)
    for dx in range(-w, w + 1):
        for dz in range(-w, w + 1):
            cv.set(dx, 0, dz, 'smooth_quartz')
            edge = max(abs(dx), abs(dz)) == w
            for y in range(1, 9):
                if edge: cv.set(dx, y, dz, 'quartz_bricks' if y % 4 else 'gold_block' if (dx + dz) % 4 == 0 else 'quartz_bricks')
            if edge and (dx + dz) % 2 == 0: cv.set(dx, 9, dz, 'quartz_bricks')
    for k, (fx, fz) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        for y in (1, 2, 3):
            for s in (-1, 0, 1): cv.set(fx * w + (s if fz else 0), y, fz * w + (s if fx else 0), None)
        cv.set(fx * w, 5, fz * w, 'light_blue_stained_glass')
    for dx, dz in ((w, w), (-w, w), (w, -w), (-w, -w)):
        castle_tower(cv, dx, 1, dz, 12, 2, 'light_blue_concrete')
    castle_tower(cv, 0, 1, 0, 16, 3, 'blue_concrete')
    for k in range(4):
        a = math.radians(45 + 90 * k + 20)
        x, z = round(Rm * 0.78 * math.cos(a)), round(Rm * 0.78 * math.sin(a))
        if (x, z) in hm: PT.oak(cv, x, hm[(x, z)] + 1, z, 6, 'birch_log', 'birch_leaves', 2.8, seed + k)

def castle_dia(cv, hm, seed):
    pillar(cv, -4, hm.get((-4, 3), 0) + 1, 3, 5, 'quartz_pillar[axis=y]'); cv.set(-4, hm.get((-4, 3), 0) + 6, 3, 'gold_block')
    birch_tree(cv, 4, hm.get((4, -4), 0) + 1, -4, seed)

# ====================================================================== 10. end city
def chorus(cv, x, y, z, seed):
    h = 4 + seed % 3; pts = set()
    for i in range(h): pts.add((x, y + i, z))
    for k, (dx, dz) in enumerate(((1, 0), (-1, 0), (0, 1))):
        by = y + 2 + k
        pts.add((x + dx, by, z + dz)); pts.add((x + dx, by + 1, z + dz))
    for (px, py, pz) in pts:
        st = {d: str((px + a, py + b, pz + c) in pts).lower() for d, (a, b, c) in
              {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0), 'up': (0, 1, 0), 'down': (0, -1, 0)}.items()}
        if (px, py - 1, pz) not in pts: st['down'] = 'true'
        cv.set(px, py, pz, 'chorus_plant[' + ','.join(f'{k}={v}' for k, v in st.items()) + ']')
    top = max(pts, key=lambda p: p[1]); cv.set(top[0], top[1] + 1, top[2], 'chorus_flower[age=5]')
    for (px, py, pz) in pts:
        if (px, py + 1, pz) not in pts and (px, py + 1, pz) != (top[0], top[1] + 1, top[2]) and py > y + 1:
            cv.set(px, py + 1, pz, 'chorus_flower[age=5]')
            st = cv.get(px, py, pz).replace('up=false', 'up=true'); cv.set(px, py, pz, st)

def end_house(cv, th, dye):
    from bwmap import cottage
    cottage(cv, th, dye)
    for dx in (-5, 5):
        cv.set(dx, 5, -7, 'end_rod[facing=up]')

def end_tower(cv, x, y, z, levels=3, w=4):
    yy = y
    for l in range(levels):
        r = w - (l % 2)
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                cv.set(x + dx, yy, z + dz, 'purpur_block')
                edge = max(abs(dx), abs(dz)) == r
                for h in range(1, 6):
                    if edge:
                        corner = abs(dx) == r and abs(dz) == r
                        cv.set(x + dx, yy + h, z + dz, 'purpur_pillar[axis=y]' if corner else ('magenta_stained_glass' if h in (2, 3) and (dx + dz) % 2 == 0 else 'purpur_block'))
                    else: cv.set(x + dx, yy + h, z + dz, None)
        for dx, dz in ((r + 1, 0), (-r - 1, 0), (0, r + 1), (0, -r - 1)):
            cv.set(x + dx, yy + 5, z + dz, 'end_rod[facing=%s]' % ('east' if dx > 0 else 'west' if dx < 0 else 'south' if dz > 0 else 'north'))
        cv.set(x, yy + 4, z, 'end_rod[facing=down]')
        yy += 6
    for dx in range(-w - 1, w + 2):
        for dz in range(-w - 1, w + 2):
            m = max(abs(dx), abs(dz))
            if m <= w + 1: cv.set(x + dx, yy, z + dz, 'purpur_slab[type=bottom]' if m == w + 1 else 'purpur_block')
    for i in range(3): cv.set(x, yy + 1 + i, z, 'purpur_pillar[axis=y]')
    cv.set(x, yy + 4, z, 'end_rod[facing=up]')

def end_mid(cv, hm, seed, Rm, em):
    end_tower(cv, 0, 1, 0, 3, 4)
    for y in (1, 2):
        for dx, dz in ((4, 0), (-4, 0), (0, 4), (0, -4)): cv.set(dx, y, dz, None)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, z = round(Rm * 0.6 * math.cos(a)), round(Rm * 0.6 * math.sin(a))
        h = 8 + (k % 2) * 3
        for i in range(h):
            for dx in (0, 1):
                for dz in (0, 1): cv.set(x + dx, 1 + i, z + dz, 'obsidian' if i % 4 else 'crying_obsidian')
        cv.set(x, 1 + h, z, 'end_rod[facing=up]')
        x2, z2 = round(Rm * 0.82 * math.cos(a + 0.4)), round(Rm * 0.82 * math.sin(a + 0.4))
        if (x2, z2) in hm: chorus(cv, x2, hm[(x2, z2)] + 1, z2, seed + k)

def end_dia(cv, hm, seed):
    for i in range(5): cv.set(-4, hm.get((-4, 3), 0) + 1 + i, 3, 'obsidian')
    cv.set(-4, hm.get((-4, 3), 0) + 6, 3, 'end_rod[facing=up]')
    chorus(cv, 4, hm.get((4, -4), 0) + 1, -4, seed)

# ====================================================================== theme table
def T(**k): return k

THEMES = [
    T(id='sakura', name='벚꽃 정원', R=84, style='home', wood='cherry', pots='sakura',
      top=[('grass_block', 8), ('moss_block', 2)], sub=[('dirt', 4), ('coarse_dirt', 1)], under=STONE, tip=[('tuff', 2), ('andesite', 1), ('cobblestone', 1)],
      hang={'body': 'hanging_roots', 'end': 'hanging_roots'},
      flora=[('pink_petals[facing=north,flower_amount=4]', 4), ('pink_petals[facing=east,flower_amount=2]', 2), ('short_grass', 4), ('fern', 1), ('lily_of_the_valley', 1), ('azure_bluet', 1), ('peony|tall', 1)],
      plaza=[('stone_bricks', 4), ('mossy_stone_bricks', 1), ('cracked_stone_bricks', 1)], path=[('gravel', 3), ('stone_bricks', 1)],
      house=dict(wall='cherry_planks', frame='dark_oak_log', floor='dark_oak_planks', roof_stair='deepslate_tile_stairs', roof_full='deepslate_tiles'),
      tree=sakura_tree, rock=[('stone', 3), ('mossy_cobblestone', 2), ('andesite', 1)], mid=sakura_mid, dia=sakura_dia,
      depth_base=20, depth_dia=15, depth_mid=28, flora_density=0.28, post='dark_oak_fence'),
    T(id='oasis', name='사막 오아시스', R=88, style='desert', wood='jungle', pots='desert',
      top=[('sand', 6), ('sandstone', 1), ('smooth_sandstone', 1)], sub=[('sandstone', 3), ('sand', 1)],
      under=[('sandstone', 4), ('smooth_sandstone', 2), ('terracotta', 1), ('orange_terracotta', 1), ('yellow_terracotta', 1)],
      tip=[('red_sandstone', 2), ('terracotta', 1)], flora_on=('sand',),
      flora=[('dead_bush', 2), ('short_dry_grass', 3), ('tall_dry_grass', 1)],
      plaza=[('smooth_sandstone', 3), ('cut_sandstone', 2), ('chiseled_sandstone', 1)], path=[('smooth_sandstone', 1)],
      house=dict(wall='smooth_sandstone', frame='cut_sandstone', floor='smooth_sandstone', roof_stair='sandstone_stairs', roof_full='cut_sandstone'),
      house_fn=desert_house, tree=palm_tree, rock=[('sandstone', 2), ('terracotta', 1), ('orange_terracotta', 1)], mid=oasis_mid, dia=oasis_dia,
      depth_base=19, depth_dia=15, depth_mid=27, flora_density=0.10, post='sandstone_wall', genpad='cut_sandstone'),
    T(id='frost', name='얼음 마을', R=92, style='frost', wood='spruce', pots='frost',
      top=[('snow_block', 8), ('white_concrete_powder', 1)], sub=[('snow_block', 1), ('dirt', 2), ('packed_ice', 1)],
      under=[('stone', 4), ('packed_ice', 2), ('andesite', 2), ('diorite', 1), ('blue_ice', 1)], tip=[('packed_ice', 2), ('blue_ice', 1)],
      flora_on=('snow_block',), flora=[('snow[layers=1]', 3), ('snow[layers=2]', 1)],
      plaza=[('polished_diorite', 3), ('diorite', 1), ('snow_block', 1)], path=[('packed_ice', 1), ('snow_block', 1)],
      house=dict(wall='spruce_planks', frame='spruce_log', floor='spruce_planks', roof_stair='spruce_stairs', roof_full='spruce_planks'),
      house_fn=cabin, tree=spruce_snow, rock=[('stone', 2), ('packed_ice', 1), ('snow_block', 1)], mid=frost_mid, dia=frost_dia,
      depth_base=20, depth_dia=15, depth_mid=28, flora_density=0.12, genpad='polished_diorite'),
    T(id='mushroom', name='버섯 숲', R=96, style='mush', wood='spruce', pots='mush',
      top=[('mycelium', 5), ('podzol', 2), ('moss_block', 1)], sub=[('dirt', 3), ('coarse_dirt', 1)],
      under=[('stone', 3), ('tuff', 2), ('dirt', 2), ('coarse_dirt', 1), ('andesite', 1)], tip=[('tuff', 2), ('stone', 1)],
      hang={'body': 'cave_vines_plant[berries=true]', 'end': 'cave_vines[age=0,berries=true]'},
      flora_on=('mycelium', 'podzol', 'moss_block'), flora=[('red_mushroom', 3), ('brown_mushroom', 3), ('fern', 2), ('short_grass', 1)],
      plaza=[('mud_bricks', 3), ('packed_mud', 1)], path=[('rooted_dirt', 1), ('coarse_dirt', 1)],
      house=dict(wall='mushroom_stem', frame='mushroom_stem', floor='spruce_planks', roof_stair='spruce_stairs', roof_full='red_mushroom_block'),
      house_fn=mush_house, tree=mush_tree, rock=[('tuff', 2), ('mossy_cobblestone', 1)], mid=mush_mid, dia=mush_dia,
      depth_base=21, depth_dia=16, depth_mid=29, flora_density=0.16, post='spruce_fence', genpad='mud_bricks'),
    T(id='harbour', name='등대 항구', R=100, style='harbour', wood='spruce', pots='home',
      top=[('grass_block', 5), ('sand', 3), ('coarse_dirt', 1)], sub=[('dirt', 3), ('sand', 1)],
      under=[('stone', 3), ('sandstone', 1), ('prismarine', 1), ('andesite', 2), ('gravel', 1)], tip=[('prismarine', 1), ('dark_prismarine', 1), ('stone', 1)],
      flora=[('short_grass', 5), ('tall_grass|tall', 1), ('dandelion', 1), ('sunflower|tall', 1)],
      plaza=[('spruce_planks', 3), ('stripped_spruce_wood[axis=y]', 1)], path=[('sand', 2), ('gravel', 1)],
      house=dict(wall='birch_planks', frame='stripped_spruce_log', floor='spruce_planks', roof_stair='dark_oak_stairs', roof_full='dark_oak_planks', stripe='concrete', trim='concrete'),
      tree=beach_tree, rock=[('stone', 2), ('andesite', 1), ('sandstone', 1)], mid=harbour_mid, dia=harbour_dia,
      depth_base=20, depth_dia=15, depth_mid=29, flora_density=0.2, genpad='smooth_stone'),
    T(id='autumn', name='가을 농장', R=104, style='farm', wood='oak', pots='home',
      top=[('grass_block', 6), ('podzol', 2), ('coarse_dirt', 1)], sub=[('dirt', 4)], under=STONE, tip=[('tuff', 1), ('stone', 1)],
      hang={'body': 'hanging_roots', 'end': 'hanging_roots'},
      flora=[('leaf_litter[facing=north,segment_amount=4]', 4), ('leaf_litter[facing=east,segment_amount=2]', 2), ('short_grass', 3), ('fern', 1), ('pumpkin', 1)],
      plaza=[('cobblestone', 2), ('mossy_cobblestone', 1), ('stone', 1)], path=[('dirt_path', 3), ('coarse_dirt', 1)],
      house=dict(wall='spruce_planks', frame='stripped_dark_oak_log', floor='oak_planks', roof_stair='dark_oak_stairs', roof_full='dark_oak_planks'),
      house_fn=barn, tree=fall_tree, rock=[('cobblestone', 2), ('mossy_cobblestone', 1), ('stone', 1)], mid=farm_mid, dia=farm_dia,
      depth_base=21, depth_dia=16, depth_mid=29, flora_density=0.25, post='oak_fence'),
    T(id='nether', name='네더 요새', R=108, style='nether', wood='crimson', pots='nether',
      top=[('netherrack', 4), ('crimson_nylium', 3), ('warped_nylium', 1), ('soul_soil', 1)], sub=[('netherrack', 4)],
      under=[('netherrack', 5), ('blackstone', 2), ('basalt[axis=y]', 2), ('magma_block', 1)], tip=[('blackstone', 2), ('basalt[axis=y]', 1)],
      hang={'body': 'weeping_vines_plant', 'end': 'weeping_vines[age=0]'},
      flora_on=('crimson_nylium', 'warped_nylium'), flora=[('crimson_roots', 3), ('warped_roots', 2), ('nether_sprouts', 2), ('crimson_fungus', 1)],
      plaza=[('nether_bricks', 3), ('cracked_nether_bricks', 1), ('red_nether_bricks', 1)], path=[('blackstone', 2), ('polished_blackstone', 1)],
      house=dict(wall='polished_blackstone_bricks', frame='chiseled_polished_blackstone', floor='nether_bricks', roof_stair='nether_brick_stairs', roof_full='nether_bricks', window='nether_brick_fence'),
      tree=fungus, rock=[('blackstone', 2), ('basalt[axis=y]', 1), ('gilded_blackstone', 1)], mid=nether_mid, dia=nether_dia,
      depth_base=22, depth_dia=16, depth_mid=30, flora_density=0.18, post='nether_brick_fence', lamp='soul_lantern', genpad='polished_blackstone'),
    T(id='jungle', name='정글 신전', R=112, style='jungle', wood='jungle', pots='jungle',
      top=[('grass_block', 6), ('moss_block', 2), ('podzol', 1)], sub=[('dirt', 4)], under=[('stone', 3), ('mossy_cobblestone', 2), ('andesite', 1), ('dirt', 1), ('tuff', 1)],
      tip=[('mossy_cobblestone', 1), ('stone', 1)], hang={'body': 'cave_vines_plant[berries=false]', 'end': 'cave_vines[age=0,berries=false]'},
      flora=[('fern', 3), ('large_fern|tall', 1), ('short_grass', 3), ('bush', 1)],
      plaza=[('mossy_stone_bricks', 3), ('stone_bricks', 2), ('cracked_stone_bricks', 1)], path=[('moss_block', 1), ('mossy_cobblestone', 1)],
      house=dict(wall='mossy_stone_bricks', frame='chiseled_stone_bricks', floor='stone_bricks', roof_stair='mossy_stone_brick_stairs', roof_full='mossy_stone_bricks'),
      tree=jungle_tree, rock=[('mossy_cobblestone', 2), ('stone', 1)], mid=jungle_mid, dia=jungle_dia,
      depth_base=22, depth_dia=16, depth_mid=31, flora_density=0.3, post='jungle_fence'),
    T(id='castle', name='천공의 성', R=116, style='castle', wood='birch', pots='castle',
      top=[('grass_block', 7), ('moss_block', 1)], sub=[('dirt', 4)], under=[('calcite', 3), ('diorite', 2), ('stone', 2), ('white_terracotta', 1)],
      tip=[('calcite', 1), ('quartz_block', 1)],
      flora=[('oxeye_daisy', 2), ('cornflower', 2), ('allium', 1), ('lily_of_the_valley', 1), ('short_grass', 4)],
      plaza=[('smooth_quartz', 3), ('quartz_bricks', 1)], path=[('smooth_quartz', 1), ('calcite', 1)],
      house=dict(wall='quartz_bricks', frame='quartz_pillar', floor='smooth_quartz', roof_stair='quartz_stairs', roof_full='quartz_block'),
      house_fn=tower_house, tree=birch_tree, rock=[('calcite', 2), ('diorite', 1)], mid=castle_mid, dia=castle_dia,
      depth_base=22, depth_dia=17, depth_mid=32, flora_density=0.25, post='birch_fence', genpad='smooth_quartz'),
    T(id='end', name='엔드 성채', R=120, style='end', wood='warped', pots='end',
      top=[('end_stone', 6), ('end_stone_bricks', 1)], sub=[('end_stone', 3)], under=[('end_stone', 5), ('obsidian', 1), ('purpur_block', 1)],
      tip=[('obsidian', 2), ('crying_obsidian', 1)], flora_on=('end_stone',), flora=[('end_rod[facing=up]', 1)],
      plaza=[('end_stone_bricks', 3), ('purpur_block', 1)], path=[('end_stone_bricks', 1)],
      house=dict(wall='purpur_block', frame='purpur_pillar', floor='end_stone_bricks', roof_stair='purpur_stairs', roof_full='purpur_block', window='magenta_stained_glass_pane'),
      house_fn=end_house, tree=chorus, rock=[('obsidian', 1), ('end_stone', 2)], mid=end_mid, dia=end_dia,
      depth_base=22, depth_dia=17, depth_mid=32, flora_density=0.03, post='end_rod', genpad='purpur_block', lamp='sea_lantern'),
]

# middle islands with furnished insides
import mids as _mids
_mids.install(THEMES)

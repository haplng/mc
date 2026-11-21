"""Middle-island centrepieces with furnished insides (they replace the first, solid versions in themes.py)."""
import math
import parts as PT
import interior as IN
from themes import ring, disc, pond, pillar, torii, stone_lantern, ice_spike, castle_tower, fungus, nether_tower, chorus, windmill as _windmill

def ladder(cv, x, y0, y1, z, facing):
    for y in range(y0, y1 + 1): cv.set(x, y, z, f'ladder[facing={facing}]')

# ---------------------------------------------------------------- 1. pagoda with three furnished floors and a central ladder post
def pagoda(cv, x, y, z, floors=3, w=5):
    yy = y; floors_y = []
    for f in range(floors):
        r = w - f
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                cv.set(x + dx, yy, z + dz, 'dark_oak_planks' if (dx + dz) % 2 else 'spruce_planks')
                edge = max(abs(dx), abs(dz)) == r
                for hh in range(1, 4):
                    if edge:
                        corner = abs(dx) == r and abs(dz) == r
                        s = 'dark_oak_log' if corner else ('white_concrete' if hh < 3 else 'cherry_planks')
                        if not corner and hh == 2 and (abs(dx) + abs(dz)) % 2 == 0: s = 'glass_pane'
                        cv.set(x + dx, yy + hh, z + dz, s)
                    else: cv.set(x + dx, yy + hh, z + dz, None)
        if f == 0:
            for dx, dz in ((r, 0), (-r, 0), (0, r), (0, -r)):
                for hh in (1, 2): cv.set(x + dx, yy + hh, z + dz, None)
        rr = r + 2; ry = yy + 4
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                m = max(abs(dx), abs(dz))
                if m == rr:
                    fa = 'south' if dz == -rr else 'north' if dz == rr else 'east' if dx == -rr else 'west'
                    cv.set(x + dx, ry, z + dz, f'deepslate_tile_stairs[facing={fa},half=bottom]')
                    if abs(dx) == rr and abs(dz) == rr: cv.set(x + dx, ry + 1, z + dz, 'deepslate_tile_slab[type=bottom]')
                elif m == rr - 1: cv.set(x + dx, ry, z + dz, 'deepslate_tiles')
                else: cv.set(x + dx, ry, z + dz, 'dark_oak_planks')
        floors_y.append((yy, r)); yy = ry
    top = yy
    # central post with a ladder through every floor
    for h in range(y + 1, top): cv.set(x, h, z, 'stripped_dark_oak_log[axis=y]')
    for fy, r in floors_y[1:]: cv.set(x + 1, fy, z, None)
    ladder(cv, x + 1, y + 1, top - 1, z, 'east')
    # ground floor: tea tables with cushions, potted bamboo, paper lanterns
    fy, r = floors_y[0]
    for tx, tz in ((-3, -3), (3, 3), (-3, 3), (3, -3)):
        cv.set(x + tx, fy + 1, z + tz, 'cherry_slab[type=bottom]')
        for cx, cz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if max(abs(tx + cx), abs(tz + cz)) < r: cv.set(x + tx + cx, fy + 1, z + tz + cz, 'pink_carpet' if (cx + cz) % 2 else 'white_carpet')
    for dx, dz in ((r - 1, r - 1), (-r + 1, r - 1), (r - 1, -r + 1), (-r + 1, -r + 1)):
        cv.set(x + dx, fy + 1, z + dz, 'potted_bamboo')
        cv.set(x + dx, fy + 3, z + dz, 'lantern[hanging=true]')
    # first floor: a library
    fy, r = floors_y[1]
    for dx in range(-r + 1, r):
        for dz in (-r + 1, r - 1):
            if abs(dx) > 1: cv.set(x + dx, fy + 1, z + dz, IN.face('bookshelf', 'south'))
    cv.set(x - 2, fy + 1, z, 'lectern[facing=east]'); cv.set(x, fy + 3, z + 2, 'lantern[hanging=true]')
    # top floor: a temple bell and incense
    fy, r = floors_y[2]
    cv.set(x - 1, fy + 1, z - 1, 'bell[attachment=floor,facing=south]'); cv.set(x - 1, fy + 1, z + 1, 'decorated_pot'); cv.set(x + 1, fy + 1, z + 1 + 0, 'potted_cherry_sapling')
    pillar(cv, x, top + 1, z, 2, 'dark_oak_fence'); cv.set(x, top + 3, z, 'lightning_rod[facing=up]')
    return top

def sakura_mid(cv, hm, seed, Rm, em):
    for xx in range(-7, 8):
        for zz in range(-7, 8): cv.set(xx, 0, zz, cv.pick([('stone_bricks', 3), ('mossy_stone_bricks', 1)]))
    pagoda(cv, 0, 1, 0, 3, 5)
    for i, (ex, ez) in enumerate(em):
        d = math.hypot(ex, ez); ux, uz = ex / d, ez / d
        tx, tz = round(ux * (d - 5)), round(uz * (d - 5))
        torii(cv, tx, 1, tz, 'z' if ex else 'x', 2, 4)
        for t in range(8, int(d) - 3):
            cv.set(round(ux * t), 0, round(uz * t), cv.pick([('gravel', 2), ('stone_bricks', 1)]))
    pond(cv, hm, round(Rm * 0.55), round(Rm * 0.6), 3, [('stone', 2), ('mossy_cobblestone', 1)], 2, 'lily_pad')
    for k in range(4):
        a = math.radians(45 + 90 * k + 18)
        xx, zz = round(Rm * 0.72 * math.cos(a)), round(Rm * 0.72 * math.sin(a))
        if (xx, zz) in hm: PT.cherry(cv, xx, hm[(xx, zz)] + 1, zz, 5, 4.2, seed + k)
    for k in range(4):
        a = math.radians(90 * k + 45)
        stone_lantern(cv, round(9.5 * math.cos(a)), 1, round(9.5 * math.sin(a)))

# ---------------------------------------------------------------- 2. pyramid with a treasure chamber
def oasis_mid(cv, hm, seed, Rm, em):
    W = max(7, int(Rm * 0.36) + 1); y = 1; lvl = 0; w = W
    while w >= 0:
        for dx in range(-w, w + 1):
            for dz in range(-w, w + 1):
                edge = max(abs(dx), abs(dz)) == w
                s = 'cut_sandstone' if lvl % 3 == 2 and edge else ('chiseled_sandstone' if edge and (dx == 0 or dz == 0) and lvl % 3 == 0 else 'sandstone')
                cv.set(dx, y, dz, s)
        w -= 1; y += 1; lvl += 1
    cv.set(0, y, 0, 'gold_block'); cv.set(0, y + 1, 0, 'lightning_rod[facing=up]')
    for k, (fx, fz, fa) in enumerate(((1, 0, 'west'), (-1, 0, 'east'), (0, 1, 'north'), (0, -1, 'south'))):
        for i in range(W + 1):
            for s in (-1, 0, 1):
                px = fx * (W - i) + (s if fz else 0); pz = fz * (W - i) + (s if fx else 0)
                cv.set(px, 1 + i, pz, f'sandstone_stairs[facing={fa},half=bottom]')
    # the chamber: 7x7, 4 high, reached by a tunnel on each diagonal-ish face
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            cv.set(dx, 1, dz, 'orange_terracotta' if (dx + dz) % 2 else 'smooth_sandstone')
            for h in range(2, 6): cv.set(dx, h, dz, None)
    for tx in range(4, W + 1):
        for h in (2, 3):
            cv.set(tx, h, -3, None); cv.set(-tx, h, 3, None)
        cv.set(tx, 1, -3, 'smooth_sandstone'); cv.set(-tx, 1, 3, 'smooth_sandstone')
    for dx, dz in ((-3, -3), (3, 3), (-3, 3), (3, -3)):
        for h in range(2, 6): cv.set(dx, h, dz, 'cut_sandstone')
        cv.set(dx, 4, dz, 'chiseled_sandstone')
    cv.set(0, 2, 0, 'gold_block'); cv.set(0, 3, 0, 'decorated_pot')
    for dx, dz, fa in ((-2, -3, 'south'), (2, -3, 'south'), (-3, 0, 'east')):
        cv.set(dx, 2, dz, f'chest[facing={fa}]')
    for dx, dz in ((2, 3), (-2, -2), (3, 1)): cv.set(dx, 2, dz, 'decorated_pot')
    for dx, dz in ((1, -1), (-1, 1)): cv.set(dx, 5, dz, 'lantern[hanging=true]')
    cv.set(-1, 2, 2, 'gold_block'); cv.set(1, 2, 2, 'gold_block'); cv.set(0, 2, 3, 'red_carpet' if False else 'gold_block')
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, z = round(Rm * 0.66 * math.cos(a)), round(Rm * 0.66 * math.sin(a))
        pillar(cv, x, 1, z, 7, 'cut_sandstone'); cv.set(x, 8, z, 'chiseled_sandstone'); cv.set(x, 9, z, 'gold_block')
    for k in range(4):
        a = math.radians(90 * k + 45)
        x, z = round(Rm * 0.84 * math.cos(a + 0.3)), round(Rm * 0.84 * math.sin(a + 0.3))
        if (x, z) in hm: PT.palm(cv, x, hm[(x, z)] + 1, z, 7, (1 if x > 0 else -1, 0), seed + k)

# ---------------------------------------------------------------- 3. ice keep with a throne hall
def frost_mid(cv, hm, seed, Rm, em):
    R = max(5, int(Rm * 0.32)); H = 10
    for y in range(1, H + 1): ring(cv, 0, y, 0, R, 'packed_ice' if y % 4 else 'blue_ice')
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            d = math.hypot(dx, dz)
            if d < R - 0.5:
                cv.set(dx, 0, dz, 'polished_diorite' if int(d) % 2 == 0 else 'light_blue_concrete')
                for y in range(1, H): cv.set(dx, y, dz, None)
    for dx, dz in ((R, 0), (-R, 0), (0, R), (0, -R)):
        for y in (1, 2, 3): cv.set(dx, y, dz, None)
    disc(cv, 0, H, 0, R, 'snow_block')
    for i, (dx, dz) in enumerate([(round(R * math.cos(a)), round(R * math.sin(a))) for a in [k * math.pi / 6 for k in range(12)]]):
        if i % 2 == 0: cv.set(dx, H + 1, dz, 'snow_block')
    for i in range(R + 4):
        r = max(0, R - 1 - i // 2)
        if r > 0: ring(cv, 0, H + 1 + i, 0, r, 'light_blue_concrete' if i % 2 == 0 else 'white_concrete', hollow=False)
        else: cv.set(0, H + 1 + i, 0, 'light_blue_concrete')
    # throne against the north wall, blue carpet runner, chandelier, barrels and benches
    cv.set(0, 1, -R + 1, 'packed_ice'); cv.set(0, 2, -R + 1, 'quartz_stairs[facing=north,half=bottom]')
    for dx in (-1, 1): cv.set(dx, 1, -R + 1, 'blue_ice'); cv.set(dx, 2, -R + 1, 'light_blue_banner[rotation=8]' if False else 'sea_lantern')
    for z in range(-R + 2, R):
        cv.set(0, 1, z, 'blue_carpet')
    for dx in (-3, 3):
        for z in (-1, 1, 3):
            if math.hypot(dx, z) < R - 1: cv.set(dx, 1, z, 'spruce_stairs[facing=%s,half=bottom]' % ('west' if dx < 0 else 'east'))
    for dx, dz in ((-R + 2, -2), (R - 2, -2), (-R + 2, 2), (R - 2, 2)):
        if math.hypot(dx, dz) < R - 0.8: cv.set(dx, 1, dz, 'barrel[facing=up]'); cv.set(dx, 2, dz, 'potted_spruce_sapling')
    for y in range(H - 3, H): cv.set(0, y, 0, 'iron_chain[axis=y]')
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)): cv.set(dx, H - 3, dz, 'lantern[hanging=false]')
    cv.set(0, H - 4, 0, 'lantern[hanging=true]')
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, z = round(Rm * 0.62 * math.cos(a)), round(Rm * 0.62 * math.sin(a))
        ice_spike(cv, x, 1, z, 7 + k % 3, 1)
        x2, z2 = round(Rm * 0.82 * math.cos(a + 0.35)), round(Rm * 0.82 * math.sin(a + 0.35))
        if (x2, z2) in hm: PT.spruce(cv, x2, hm[(x2, z2)] + 1, z2, 9, snow=True)
    for ex, ez in em:
        sx = (ex > 0) - (ex < 0); sz = (ez > 0) - (ez < 0)
        for t in range(R + 1, int(math.hypot(ex, ez)) - 2):
            for s in (-1, 0, 1):
                cv.set(sx * t + (s if sz else 0), 0, sz * t + (s if sx else 0), 'blue_ice' if s == 0 else 'packed_ice')

# ---------------------------------------------------------------- 5. lighthouse you can climb
def lighthouse(cv, x, y, z, H=18, R=3):
    for i in range(H):
        ring(cv, x, y + i, z, R, 'red_concrete' if (i // 3) % 2 else 'white_concrete')
        disc(cv, x, y + i, z, R - 1, 'air') if False else None
    for dx in range(-R + 1, R):
        for dz in range(-R + 1, R):
            if math.hypot(dx, dz) < R - 0.5:
                cv.set(x + dx, y - 1, z + dz, 'spruce_planks')
                for i in range(H): cv.set(x + dx, y + i, z + dz, None)
    for i in (0, 1): cv.set(x + R, y + i, z, None)
    top = y + H
    disc(cv, x, top, z, R + 1, 'spruce_planks'); ring(cv, x, top + 1, z, R + 1, 'spruce_fence')
    ring(cv, x, top + 1, z, R - 1, 'light_blue_stained_glass'); ring(cv, x, top + 2, z, R - 1, 'light_blue_stained_glass')
    cv.set(x, top + 1, z, 'sea_lantern'); cv.set(x, top + 2, z, 'sea_lantern')
    for i in range(4):
        r = R - 1 - i
        if r < 0: break
        if r > 0: disc(cv, x, top + 3 + i, z, r, 'red_concrete')
        else: cv.set(x, top + 3 + i, z, 'red_concrete')
    cv.set(x, top + 3 + R, z, 'lightning_rod[facing=up]')
    # ladder on the west wall up to the lamp room, a hole in the floor up there
    ladder(cv, x - R + 1, y, top, z, 'east')
    cv.set(x - R + 1, top, z, None); ladder(cv, x - R + 1, top, top, z, 'east')
    ring(cv, x, top + 1, z, R - 1, 'light_blue_stained_glass')
    cv.set(x - R + 1, top + 1, z, None); cv.set(x - R + 1, top + 2, z, None)
    # ground floor: a keeper's corner
    cv.set(x + 1, y, z - 1, 'barrel[facing=up]'); cv.set(x + 1, y + 1, z - 1, 'potted_fern')
    cv.set(x, y, z + 1, 'cartography_table'); cv.set(x + 1, y, z + 1, 'chest[facing=west]')
    cv.set(x, y + 3, z, 'lantern[hanging=true]')

def harbour_mid(cv, hm, seed, Rm, em):
    lighthouse(cv, 0, 1, 0, 16 + Rm // 6, 3)
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
                if (x + dx, z + dz) in hm: cv.set(x + dx, hm[(x + dx, z + dz)] + 1, z + dz, 'barrel[facing=up]')
        x2, z2 = round(Rm * 0.86 * math.cos(a + 0.4)), round(Rm * 0.86 * math.sin(a + 0.4))
        if (x2, z2) in hm: PT.palm(cv, x2, hm[(x2, z2)] + 1, z2, 7, (1 if x2 > 0 else -1, 0), seed + k)

# ---------------------------------------------------------------- 6. windmill with a mill room
def windmill(cv, x, y, z, H=12):
    _windmill(cv, x, y, z, H)
    # hollow body (the base ring is cobblestone, r=4; the body r=3), a floor, a ladder, the mill room
    for i in range(H):
        r = 4 if i < 3 else 3 if i < 8 else 2
        for dx in range(-r + 1, r):
            for dz in range(-r + 1, r):
                if math.hypot(dx, dz) < r - 0.5: cv.set(x + dx, y + i, z + dz, None)
    disc(cv, x, y - 1, z, 3, 'spruce_planks')
    for i in (0, 1): cv.set(x + 4, y + i, z, None); cv.set(x + 3, y + i, z, None)
    ladder(cv, x - 1, y, y + H - 1, z, 'east') if False else None
    cv.set(x, y, z, 'grindstone[face=floor,facing=east]')
    cv.set(x - 2, y, z - 1, 'barrel[facing=up]'); cv.set(x - 2, y + 1, z - 1, 'potted_dandelion' if False else 'potted_fern')
    cv.set(x - 2, y, z + 1, 'hay_block[axis=y]'); cv.set(x - 1, y, z + 2, 'hay_block[axis=x]'); cv.set(x - 2, y + 1, z + 1, 'hay_block[axis=z]')
    cv.set(x + 1, y, z - 2, 'composter'); cv.set(x + 1, y, z + 2, 'chest[facing=north]')
    cv.set(x - 1, y, z - 2, 'smoker[facing=south]')
    for i in range(y + 2, y + H - 1): cv.set(x, i, z, 'stripped_spruce_log[axis=y]')
    cv.set(x + 1, y + 3, z, 'lantern[hanging=false]') if False else cv.set(x, y + H - 2, z + 1, 'lantern[hanging=true]')

def farm_mid(cv, hm, seed, Rm, em):
    windmill(cv, 0, 1, 0, 11 + Rm // 8)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x0, z0 = round(Rm * 0.62 * math.cos(a)), round(Rm * 0.62 * math.sin(a))
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                p = (x0 + dx, z0 + dz)
                if p in hm:
                    y = hm[p]; cv.set(p[0], y, p[1], 'farmland[moisture=7]')
                    cv.set(p[0], y + 1, p[1], 'pumpkin' if cv.rng.random() < 0.25 else 'wheat[age=7]' if k % 2 else 'carrots[age=7]')
        x1, z1 = round(Rm * 0.86 * math.cos(a + 0.4)), round(Rm * 0.86 * math.sin(a + 0.4))
        if (x1, z1) in hm: PT.autumn_tree(cv, x1, hm[(x1, z1)] + 1, z1, 6, 3.6, seed + k)
        x2, z2 = round(Rm * 0.45 * math.cos(a - 0.5)), round(Rm * 0.45 * math.sin(a - 0.5))
        if (x2, z2) in hm:
            cv.set(x2, hm[(x2, z2)] + 1, z2, 'hay_block[axis=y]'); cv.set(x2 + 1, hm[(x2, z2)] + 1, z2, 'hay_block[axis=x]')
            cv.set(x2, hm[(x2, z2)] + 2, z2, 'hay_block[axis=z]')

# ---------------------------------------------------------------- 7. nether fortress with tower rooms
def nether_mid(cv, hm, seed, Rm, em):
    for dx in range(-5, 6):
        for dz in range(-5, 6):
            d = math.hypot(dx, dz)
            if d < 3.5:
                cv.set(dx, 0, dz, 'lava'); cv.set(dx, -1, dz, 'blackstone'); cv.set(dx, -2, dz, 'blackstone')
            elif d < 5:
                cv.set(dx, 0, dz, 'polished_blackstone_bricks')
                if d >= 4.5: cv.set(dx, 1, dz, 'polished_blackstone_brick_wall')
    rt = Rm * 0.42
    towers = []
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, z = round(rt * math.cos(a)), round(rt * math.sin(a))
        nether_tower(cv, x, 1, z, 11 + k % 2 * 2, 2); towers.append((x, z))
        # door toward the middle and a little room inside
        sx = -1 if x > 0 else 1; sz = -1 if z > 0 else 1
        for h in (1, 2): cv.set(x + 2 * sx, h, z, None)
        cv.set(x, 1, z, 'brewing_stand'); cv.set(x - sx, 1, z - sz, 'barrel[facing=up]'); cv.set(x - sx, 2, z - sz, 'potted_crimson_fungus')
        cv.set(x + sx, 1, z - sz, 'blackstone_slab[type=top]') if False else cv.set(x, 1, z - sz, 'polished_blackstone_stairs[facing=%s,half=bottom]' % ('north' if sz > 0 else 'south'))
        for h in range(5, 9): cv.set(x, h, z, 'iron_chain[axis=y]')
        cv.set(x, 4, z, 'soul_lantern[hanging=true]')
    for i in range(4):
        (x0, z0), (x1, z1) = towers[i], towers[(i + 1) % 4]
        PT.trunk_line(cv, x0, 9, z0, x1, 9, z1, 'nether_bricks')
        PT.trunk_line(cv, x0, 10, z0, x1, 10, z1, 'nether_brick_fence')
    for k in range(6):
        a = math.radians(15 + 60 * k)
        x, z = round(Rm * 0.82 * math.cos(a)), round(Rm * 0.82 * math.sin(a))
        if (x, z) in hm: fungus(cv, x, hm[(x, z)] + 1, z, seed + k, 7 + k % 3)

# ---------------------------------------------------------------- 8. jungle temple with a treasure room
def temple(cv, x, y, z, w, steps):
    yy = y
    for s in range(steps):
        r = w - s * 2; hgt = 4 if s == 0 else 2
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                for h in range(hgt):
                    edge = max(abs(dx), abs(dz)) >= r - (0 if s == 0 else 1)
                    if edge or h == 0:
                        cv.set(x + dx, yy + h, z + dz, cv.pick([('mossy_stone_bricks', 3), ('stone_bricks', 2), ('cracked_stone_bricks', 1), ('mossy_cobblestone', 1)]))
                    else: cv.set(x + dx, yy + h, z + dz, None)
        for k, (fx, fz, fa) in enumerate(((1, 0, 'west'), (-1, 0, 'east'), (0, 1, 'north'), (0, -1, 'south'))):
            for t in range(hgt):
                for sd in (-1, 0, 1):
                    px = x + fx * (r + hgt - 1 - t) + (sd if fz else 0); pz = z + fz * (r + hgt - 1 - t) + (sd if fx else 0)
                    cv.set(px, yy + t, pz, f'mossy_stone_brick_stairs[facing={fa},half=bottom]')
        if s == 0:
            # the treasure room on the ground floor: doors on two sides beside the stairs
            for h in (1, 2): cv.set(x + r, yy + h, z - 3, None); cv.set(x - r, yy + h, z + 3, None)
            cv.set(x, yy + 1, z, 'gold_block'); cv.set(x, yy + 2, z, 'decorated_pot')
            for dx, dz, fa in ((-2, -r + 1, 'south'), (2, -r + 1, 'south'), (-r + 1, 0, 'east')):
                cv.set(x + dx, yy + 1, z + dz, f'chest[facing={fa}]')
            for dx, dz in ((r - 1, r - 1), (-r + 1, -r + 1), (r - 1, -r + 1), (-r + 1, r - 1)):
                cv.set(x + dx, yy + 1, z + dz, 'chiseled_stone_bricks'); cv.set(x + dx, yy + 2, z + dz, 'candle[candles=3,lit=true]')
            for dx, dz in ((2, 2), (-2, 2), (2, -2)):
                cv.set(x + dx, yy + 1, z + dz, 'decorated_pot')
            cv.set(x + 1, yy + 3, z + 1, 'lantern[hanging=true]'); cv.set(x - 1, yy + 3, z - 1, 'lantern[hanging=true]')
        yy += hgt
    r = max(2, w - steps * 2)
    for dx, dz in ((r, r), (-r, r), (r, -r), (-r, -r)): pillar(cv, x + dx, yy, z + dz, 4, 'chiseled_stone_bricks')
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1): cv.set(x + dx, yy + 4, z + dz, 'mossy_stone_brick_slab[type=bottom]')
    cv.set(x, yy, z, 'gold_block'); cv.set(x, yy + 3, z, 'lantern[hanging=true]')
    return yy

def jungle_mid(cv, hm, seed, Rm, em):
    temple(cv, 0, 1, 0, max(7, int(Rm * 0.36)), 3)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, z = round(Rm * 0.74 * math.cos(a)), round(Rm * 0.74 * math.sin(a))
        if (x, z) in hm: PT.big_oak(cv, x, hm[(x, z)] + 1, z, 9, 'jungle_log', 'jungle_leaves', 5.0, seed + k)
    for (x, y, z), s in list(cv.b.items()):
        if ('stone_bricks' in s or 'cobblestone' in s) and y > 1 and cv.rng.random() < 0.08:
            for dx, dz, fa in ((1, 0, 'west'), (-1, 0, 'east'), (0, 1, 'north'), (0, -1, 'south')):
                if cv.empty(x + dx, y, z + dz):
                    for i in range(cv.rng.randint(1, 3)):
                        if cv.empty(x + dx, y - i, z + dz): cv.set(x + dx, y - i, z + dz, f'vine[{fa}=true]')
                    break

# ---------------------------------------------------------------- 9. castle keep with a throne hall
def castle_mid(cv, hm, seed, Rm, em):
    w = max(6, int(Rm * 0.32)); H = 9
    for dx in range(-w, w + 1):
        for dz in range(-w, w + 1):
            cv.set(dx, 0, dz, 'smooth_quartz' if (dx + dz) % 2 else 'quartz_bricks')
            edge = max(abs(dx), abs(dz)) == w
            for y in range(1, H):
                if edge: cv.set(dx, y, dz, 'quartz_bricks' if y % 4 else 'gold_block' if (dx + dz) % 4 == 0 else 'quartz_bricks')
                else: cv.set(dx, y, dz, None)
            cv.set(dx, H, dz, 'smooth_quartz')
            if edge and (dx + dz) % 2 == 0: cv.set(dx, H + 1, dz, 'quartz_bricks')
    for k, (fx, fz) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        for y in (1, 2, 3):
            for s in (-1, 0, 1): cv.set(fx * w + (s if fz else 0), y, fz * w + (s if fx else 0), None)
        for s in (-2, 2): cv.set(fx * w + (s if fz else 0), 5, fz * w + (s if fx else 0), 'light_blue_stained_glass')
    for dx, dz in ((w, w), (-w, w), (w, -w), (-w, -w)): castle_tower(cv, dx, 1, dz, 12, 2, 'light_blue_concrete')
    castle_tower(cv, 0, H + 1, 0, 7, 3, 'blue_concrete')
    # throne hall: red runner, gold throne, team banners, chandeliers, benches
    cv.set(0, 1, -w + 1, 'gold_block'); cv.set(0, 2, -w + 1, 'quartz_stairs[facing=north,half=bottom]')
    cv.set(-1, 1, -w + 1, 'quartz_stairs[facing=east,half=bottom]'); cv.set(1, 1, -w + 1, 'quartz_stairs[facing=west,half=bottom]')
    for z in range(-w + 2, w): cv.set(0, 1, z, 'red_carpet')
    dyes = ['red', 'blue', 'lime', 'yellow', 'cyan', 'white', 'pink', 'gray']
    for i, z in enumerate(range(-w + 2, w - 1, 2)):
        if i < 4:
            cv.set(-w + 1, 4, z, f'{dyes[i]}_wall_banner[facing=east]'); cv.set(w - 1, 4, z, f'{dyes[i + 4]}_wall_banner[facing=west]')
    for dx in (-3, 3):
        for z in range(-w + 3, w - 1, 2): cv.set(dx, 1, z, 'birch_stairs[facing=%s,half=bottom]' % ('west' if dx < 0 else 'east'))
    for dx, dz in ((-3, -2), (3, -2), (-3, 2), (3, 2)):
        if abs(dx) < w and abs(dz) < w:
            cv.set(dx, H - 1, dz, 'iron_chain[axis=y]'); cv.set(dx, H - 2, dz, 'lantern[hanging=true]')
    for dx in range(-w + 1, w):
        if abs(dx) > 1: cv.set(dx, 1, -w + 1, IN.face('bookshelf', 'south')) if abs(dx) > 2 else None
    for k in range(4):
        a = math.radians(45 + 90 * k + 20)
        x, z = round(Rm * 0.8 * math.cos(a)), round(Rm * 0.8 * math.sin(a))
        if (x, z) in hm: PT.oak(cv, x, hm[(x, z)] + 1, z, 6, 'birch_log', 'birch_leaves', 2.8, seed + k)

# ---------------------------------------------------------------- 10. end tower with furnished floors and a ladder
def end_tower(cv, x, y, z, levels=3, w=4):
    yy = y; lv = []
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
        lv.append((yy, r)); yy += 6
    for dx in range(-w - 1, w + 2):
        for dz in range(-w - 1, w + 2):
            m = max(abs(dx), abs(dz))
            if m <= w + 1: cv.set(x + dx, yy, z + dz, 'purpur_slab[type=bottom]' if m == w + 1 else 'purpur_block')
    for i in range(3): cv.set(x, yy + 1 + i, z, 'purpur_pillar[axis=y]')
    cv.set(x, yy + 4, z, 'end_rod[facing=up]')
    # ladder in the north-west corner, through every floor, and things on each floor
    for (fy, r) in lv:
        cv.set(x - r + 1, fy + 1, z - r + 1, None)
    lx, lz = x - 2, z - 2
    for (fy, r) in lv[1:]: cv.set(lx, fy, lz, None)
    cv.set(lx, yy, lz, None)
    ladder(cv, lx, y + 1, yy, lz, 'south') if False else None
    for h in range(y + 1, yy + 1): cv.set(lx, h, lz - 1, cv.get(lx, h, lz - 1) or 'purpur_block')
    ladder(cv, lx, y + 1, yy, lz, 'south')
    items = [('brewing_stand', 'magenta_shulker_box[facing=up]', 'purpur_stairs[facing=west,half=bottom]'),
             ('enchanting_table', 'purple_shulker_box[facing=up]', 'end_stone_brick_wall'),
             ('lectern[facing=west]', 'magenta_shulker_box[facing=up]', 'purpur_stairs[facing=east,half=bottom]')]
    for (fy, r), (a, b, c) in zip(lv, items):
        cv.set(x + 2, fy + 1, z + 2, a); cv.set(x + 2, fy + 1, z - 1, b); cv.set(x - 1, fy + 1, z + 2, c)
        cv.set(x, fy + 4, z, 'end_rod[facing=down]')

def end_mid(cv, hm, seed, Rm, em):
    end_tower(cv, 0, 1, 0, 3, 4)
    for y in (2, 3):
        for dx, dz in ((4, 0), (-4, 0), (0, 4), (0, -4)): cv.set(dx, y, dz, None)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, z = round(Rm * 0.62 * math.cos(a)), round(Rm * 0.62 * math.sin(a))
        h = 8 + (k % 2) * 3
        for i in range(h):
            for dx in (0, 1):
                for dz in (0, 1): cv.set(x + dx, 1 + i, z + dz, 'obsidian' if i % 4 else 'crying_obsidian')
        cv.set(x, 1 + h, z, 'end_rod[facing=up]')
        x2, z2 = round(Rm * 0.84 * math.cos(a + 0.4)), round(Rm * 0.84 * math.sin(a + 0.4))
        if (x2, z2) in hm: chorus(cv, x2, hm[(x2, z2)] + 1, z2, seed + k)

def install(THEMES):
    by = {t['id']: t for t in THEMES}
    by['sakura']['mid'] = sakura_mid; by['oasis']['mid'] = oasis_mid; by['frost']['mid'] = frost_mid
    by['harbour']['mid'] = harbour_mid; by['autumn']['mid'] = farm_mid; by['nether']['mid'] = nether_mid
    by['jungle']['mid'] = jungle_mid; by['castle']['mid'] = castle_mid; by['end']['mid'] = end_mid

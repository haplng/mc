"""Bed wars map layout: 8 team bases, 4 diamond islands, a middle island with emerald generators, side islands."""
import math
from canvas import Canvas, rot_xz
import parts as PT
import interior as IN
from scipy.spatial import cKDTree
import numpy as np

TEAMS = [('red', 'red'), ('blue', 'blue'), ('green', 'lime'), ('yellow', 'yellow'),
         ('aqua', 'cyan'), ('white', 'white'), ('pink', 'pink'), ('gray', 'gray')]

def tc(team_dye, kind):
    return f'{team_dye}_{kind}'

# ------------------------------------------------------------------ team base (local frame: +z points to the middle)
def cottage(cv, th, dye, x0=-5, x1=5, z0=-14, z1=-8, h=4):
    """default base house: frame + walls + gable roof, door facing +z"""
    P = th['house']
    wall, frame, floor = P['wall'], P['frame'], P['floor']
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            cv.set(x, 0, z, floor)
            for y in range(1, h + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                corner = x in (x0, x1) and z in (z0, z1)
                if not edge: cv.set(x, y, z, None); continue
                cv.set(x, y, z, frame if corner or y == h else wall)
    # team-coloured stripe and windows
    for x in range(x0 + 1, x1):
        cv.set(x, h, z1, tc(dye, P.get('stripe', 'wool'))); cv.set(x, h, z0, tc(dye, P.get('stripe', 'wool')))
    for x in (x0 + 2, x1 - 2):
        cv.set(x, 2, z1, P.get('window', 'glass_pane')); cv.set(x, 2, z0, P.get('window', 'glass_pane'))
    for z in range(z0 + 2, z1 - 1, 3):
        cv.set(x0, 2, z, P.get('window', 'glass_pane')); cv.set(x1, 2, z, P.get('window', 'glass_pane'))
    # door opening
    mid = (x0 + x1) // 2
    for y in (1, 2): cv.set(mid, y, z1, None)
    cv.set(mid, 3, z1 + 1, f'{dye}_banner[rotation=0]'.replace('banner[rotation=0]', 'wall_banner[facing=south]'))
    # roof
    rs = P['roof_stair']; rf = P['roof_full']
    PT.roof_gable(cv, x0, x1, z0, z1, h + 1, rs, rf, trim=tc(dye, P.get('trim', 'wool')), axis='x')
    cv.set(mid, h, (z0 + z1) // 2, 'lantern[hanging=true]')
    IN.room(cv, x0 + 1, x1 - 1, z0 + 1, z1 - 1, 1, dye, th.get('style', 'home'), th.get('wood', 'oak'), th.get('pots', 'home'), door=(mid, z1 - 1), h=h - 1)

def team_base(th, dye, seed, size=1.0):
    cv = Canvas(seed)
    rx = int(round(13 * size)); rz = int(round(16 * size))
    hm = PT.island(cv, 0, 0, -2, rx, rz, th['depth_base'] * size, th, seed, flat=0.66, hill=th.get('hill', 1.4))
    PT.flatten(cv, hm, -8, -10, 8, 10, 0, th)
    plaza = th['plaza']
    # spawn plaza, path, bed platform
    for x in range(-3, 4):
        for z in range(-3, 3): cv.set(x, 0, z, cv.pick(plaza))
    for z in range(3, 6):
        for x in (-1, 0, 1): cv.set(x, 0, z, cv.pick(th['path']))
    for x in range(-2, 3):
        for z in range(6, 11): cv.set(x, 0, z, cv.pick(plaza))
    for x in (-2, 2):
        for z in (6, 10): cv.set(x, 0, z, tc(dye, 'concrete'))
    cv.set(0, 1, 8, f'{dye}_bed[facing=south,part=foot]'); cv.set(0, 1, 9, f'{dye}_bed[facing=south,part=head]')
    # generator pad (iron / gold) behind the spawn
    for x in (-1, 0, 1):
        for z in (-6, -5, -4): cv.set(x, 0, z, th.get('genpad', 'polished_andesite'))
    cv.set(0, 0, -5, th.get('gencore', 'iron_block'))
    for x in (-2, 2):
        for z in (-6, -5, -4): cv.set(x, 0, z, tc(dye, 'concrete'))
    cv.set(-3, 1, -4, 'chest[facing=south]'); cv.set(3, 1, -4, 'ender_chest[facing=south]')
    # shop corners: a little stand on each side
    for sx in (-6, 6):
        cv.set(sx, 0, 1, cv.pick(plaza))
        for dz in (-1, 0, 1):
            cv.set(sx, 0, 1 + dz, cv.pick(plaza))
        cv.set(sx + (1 if sx < 0 else -1), 0, 1, cv.pick(plaza))
    # lanterns on the plaza corners
    for x, z in ((-4, -3), (4, -3), (-3, 10), (3, 10)):
        PT.lantern_post(cv, x, 1, z, th.get('post', 'spruce_fence'), th.get('lamp', 'lantern'), 2)
    # house (theme may replace it) on flattened ground
    PT.flatten(cv, hm, -7, -16, 7, -7, 0, th)
    (th.get('house_fn') or cottage)(cv, th, dye)
    IN.forge(cv, th, dye)
    # decoration around the edge
    rng = cv.rng
    spots = [(-10, -4), (10, -5), (-9, 4), (9, 5), (-6, -16), (6, -16), (-11, -11), (11, -11)]
    for i, (x, z) in enumerate(spots):
        if (x, z) not in hm: continue
        y = hm[(x, z)]
        if i % 3 == 2 and th.get('rock'):
            PT.boulder(cv, x, y + 1, z, 1.8, th['rock'], seed + i)
        else:
            th['tree'](cv, x, y + 1, z, seed + i)
    PT.flora(cv, hm, th, th.get('flora_density', 0.2), avoid=lambda x, z: -4 <= x <= 4 and -7 <= z <= 11)
    # markers for the game logic
    tags = ['bw', 'bw.team', 'bw.t.' + dye]
    cv.marker(0, 1, 0, tags + ['bw.spawn'])
    cv.marker(0, 1, 8, tags + ['bw.bed'])
    cv.marker(0, 1, -5, tags + ['bw.gen', 'bw.gen.iron'])
    cv.marker(-6, 1, 1, tags + ['bw.shop'])
    cv.marker(6, 1, 1, tags + ['bw.upgrade'])
    for (x, y, z) in list(cv.b):   # the bed area must stay clear of decoration
        pass
    return cv

# ------------------------------------------------------------------ generator islands
def gen_ring(cv, x, y, z, core, ring, rim):
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            d = max(abs(dx), abs(dz))
            cv.set(x + dx, y, z + dz, core if d == 0 else (ring if d == 1 else rim))
            for yy in (1, 2, 3):
                if d <= 1: cv.set(x + dx, y + yy, z + dz, None)

def diamond_island(th, seed, size=1.0):
    cv = Canvas(seed)
    r = 8 * size
    hm = PT.island(cv, 0, 0, 0, r, r * 0.9, th['depth_dia'] * size, th, seed, flat=0.5, hill=1.2)
    gen_ring(cv, 0, 0, 0, 'diamond_block', th.get('genpad', 'polished_andesite'), cv.pick(th['plaza']))
    IN.shrine(cv, th, 0, 0, 'diamond_block', 'light_blue_stained_glass')
    cv.marker(0, 1, 0, ['bw', 'bw.gen', 'bw.gen.diamond'])
    th['dia'](cv, hm, seed)
    PT.flora(cv, hm, th, th.get('flora_density', 0.2) * 0.8, avoid=lambda x, z: abs(x) <= 2 and abs(z) <= 2)
    return cv

def side_island(th, seed, size=1.0):
    cv = Canvas(seed)
    r = 6 * size
    hm = PT.island(cv, 0, 0, 0, r, r * 0.85, th['depth_dia'] * 0.9, th, seed, flat=0.3, hill=1.6)
    (th.get('side') or th['dia'])(cv, hm, seed + 5)
    PT.flora(cv, hm, th, th.get('flora_density', 0.2))
    return cv

def mid_island(th, seed, Rm):
    cv = Canvas(seed)
    hm = PT.island(cv, 0, 0, 0, Rm, Rm * 0.95, th['depth_mid'], th, seed, flat=0.75, hill=1.5)
    PT.flatten(cv, hm, -int(Rm * 0.55), -int(Rm * 0.55), int(Rm * 0.55), int(Rm * 0.55), 0, th)
    e = int(round(Rm * 0.62))
    em = [(e, 0), (-e, 0), (0, e), (0, -e)]
    for i, (x, z) in enumerate(em):
        gen_ring(cv, x, 0, z, 'emerald_block', th.get('genpad', 'polished_andesite'), cv.pick(th['plaza']))
        cv.marker(x, 1, z, ['bw', 'bw.gen', 'bw.gen.emerald'])
    th['mid'](cv, hm, seed, Rm, em)
    for (x, z) in em:      # emerald shrines go in last so nothing of the centrepiece sits inside them
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                for y in range(1, 8): cv.set(x + dx, y, z + dz, None)
        gen_ring(cv, x, 0, z, 'emerald_block', th.get('genpad', 'polished_andesite'), cv.pick(th['plaza']))
        IN.shrine(cv, th, x, z, 'emerald_block', 'lime_stained_glass')
    PT.flora(cv, hm, th, th.get('flora_density', 0.2), avoid=lambda x, z: any(abs(x - a) <= 2 and abs(z - b) <= 2 for a, b in em))
    return cv

# ------------------------------------------------------------------ whole map
def footprint(c, dx, dz, k):
    pts = set()
    for (x, y, z) in c.b:
        rx, rz = rot_xz(x, z, k); pts.add((rx + dx, rz + dz))
    return pts

def build_map(th, R, seed=1, Y0=0):
    cv = Canvas(seed)
    cv.feet = []                                # 2D footprints of every island, to measure the gaps
    size = 0.95 + (R - 84) / 36 * 0.15          # islands grow a little with the map
    for k, (team, dye) in enumerate(TEAMS):
        a = math.radians(22.5 + 45 * k)
        bx, bz = round(R * math.cos(a)), round(R * math.sin(a))
        inward = (-math.cos(a), -math.sin(a))
        best = max(range(4), key=lambda r: (rot_xz(0, 1, r)[0] * inward[0] + rot_xz(0, 1, r)[1] * inward[1]))
        base = team_base(th, dye, seed * 7 + 1, size)          # same seed: all bases identical except colours
        cv.overlap = getattr(cv, 'overlap', 0) + cv.paste(base, bx, Y0, bz, best); cv.feet.append(footprint(base, bx, bz, best))
    Rd = round(R * 0.53)
    for k in range(4):
        a = math.radians(90 * k)
        isl = diamond_island(th, seed * 11 + k, size); px, pz = round(Rd * math.cos(a)), round(Rd * math.sin(a))
        cv.overlap = getattr(cv, 'overlap', 0) + cv.paste(isl, px, Y0 + th.get('dia_dy', -1), pz, k); cv.feet.append(footprint(isl, px, pz, k))
    Rs = round(R * 0.645)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        isl = side_island(th, seed * 13 + k, size); px, pz = round(Rs * math.cos(a)), round(Rs * math.sin(a))
        cv.overlap = getattr(cv, 'overlap', 0) + cv.paste(isl, px, Y0 + th.get('side_dy', 2), pz, k); cv.feet.append(footprint(isl, px, pz, k))
    Rm = int(round(17 + (R - 84) * 0.25))
    isl = mid_island(th, seed * 17, Rm)
    cv.overlap = getattr(cv, 'overlap', 0) + cv.paste(isl, 0, Y0 + th.get('mid_dy', 1), 0, 0); cv.feet.append(footprint(isl, 0, 0, 0))
    return cv

def gaps(cv):
    """smallest open-air distance between any two islands (seen from above)"""
    trees = [cKDTree(np.array(sorted(f))) for f in cv.feet]
    arrs = [np.array(sorted(f)) for f in cv.feet]
    best = 1e9
    for i in range(len(arrs)):
        for j in range(i + 1, len(arrs)):
            d, _ = trees[j].query(arrs[i], k=1)
            best = min(best, float(d.min()))
    return best

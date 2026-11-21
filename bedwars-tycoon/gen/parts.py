"""Building blocks for floating-island bed wars maps: islands, trees, rocks, flora, small buildings."""
import math
from canvas import Canvas

LEAF = lambda s: s + '[persistent=true]' if 'leaves' in s and '[' not in s else s

# ------------------------------------------------------------------ islands
def island(cv, cx, cy, cz, rx, rz, depth, th, seed, flat=0.0, hill=1.5, rough=0.22, top_override=None):
    """Organic floating island. Top surface at cy (plus gentle hills outside the flat core); the underside is a
    rocky mass that narrows towards the bottom, in layered bands of the theme's rock, with a few hanging spikes.
    Returns {(x, z): top_y}."""
    nz = cv.noise; hm = {}
    so = seed * 131.7
    strata = th.get('strata') or [s for s, w in th['under'] for _ in range(max(1, int(w)))]
    for x in range(int(cx - rx - 4), int(cx + rx + 5)):
        for z in range(int(cz - rz - 4), int(cz + rz + 5)):
            dx = (x - cx) / rx; dz = (z - cz) / rz; d = math.sqrt(dx * dx + dz * dz)
            n = nz.f2(x + so, z - so, 9.0)
            d2 = d + (n - 0.5) * rough * 2.2
            if d2 >= 1.0: continue
            core = d2 < flat
            bump = 0 if core else int(round((nz.f2(x - so, z + so, 6.0) - 0.42) * 2 * hill * min(1.0, (d2 - flat) / 0.25 + 0.2)))
            if d2 > 0.93: bump = min(bump, 0)
            ty = cy + max(-1, bump)
            smooth = nz.f2(x * 0.9 + so, z * 0.9 - so, 7.0, 3)
            dep = depth * (1 - d2) ** 0.55 * (0.7 + 0.6 * smooth) + 2
            # hanging spikes here and there
            sp = nz.n2(x * 3.1 - so, z * 3.1 + so, 2.0)
            if sp > 0.78 and d2 < 0.85: dep += (sp - 0.78) * 30 * (1 - d2)
            by = int(cy - dep)
            for y in range(by, ty + 1):
                if y == ty: b = top_override or cv.pick(th['top'])
                elif ty - y <= th.get('sub_n', 3): b = cv.pick(th['sub'])
                elif y - by <= 1: b = cv.pick(th['tip'])
                else:
                    band = int((y + nz.n2(x * 0.7, z * 0.7 + y * 0.1, 5.0) * 5) // 3)
                    b = strata[band % len(strata)] if cv.rng.random() < 0.85 else cv.pick(th['under'])
                cv.set(x, y, z, b)
            hm[(x, z)] = ty
            if d2 > 0.55 and th.get('hang') and cv.rng.random() < 0.10:
                ln = cv.rng.randint(1, 4); h = th['hang']
                for i in range(1, ln + 1):
                    yy = ty - th.get('sub_n', 3) - 1 - i if False else by - i
                    if not cv.empty(x, yy, z): break
                    cv.set(x, yy, z, h['body'] if i < ln else h['end'])
    return hm

def flatten(cv, hm, x0, z0, x1, z1, y, th):
    """make a flat walkable patch at height y (fills up or cuts down)"""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x, z) not in hm: continue
            ty = hm[(x, z)]
            for yy in range(y + 1, ty + 4): cv.set(x, yy, z, None)
            for yy in range(min(ty, y), y):
                if cv.empty(x, yy, z): cv.set(x, yy, z, cv.pick(th['sub']))
            cv.set(x, y, z, cv.pick(th['top'])); hm[(x, z)] = y

def flora(cv, hm, th, density=0.18, avoid=None):
    for (x, z), y in hm.items():
        if avoid and avoid(x, z): continue
        if not cv.empty(x, y + 1, z): continue
        top = cv.get(x, y, z) or ''
        if not any(t in top for t in th.get('flora_on', ('grass_block', 'moss_block', 'podzol', 'dirt'))): continue
        if cv.rng.random() < density:
            s = cv.pick(th['flora'])
            if s.endswith('|tall'):
                b = s[:-5]; cv.set(x, y + 1, z, b + '[half=lower]'); cv.set(x, y + 2, z, b + '[half=upper]')
            else:
                cv.set(x, y + 1, z, s)

# ------------------------------------------------------------------ rocks and trees
def boulder(cv, x, y, z, r, mix, seed=0, squash=0.8):
    nz = cv.noise
    R = int(math.ceil(r)) + 1
    for dx in range(-R, R + 1):
        for dy in range(-R, R + 1):
            for dz in range(-R, R + 1):
                d = math.sqrt(dx * dx + (dy / squash) ** 2 + dz * dz)
                if d + (nz.n3(x + dx + seed, y + dy, z + dz, 2.5) - 0.5) * 1.6 < r:
                    cv.set(x + dx, y + dy, z + dz, cv.pick(mix))

def blob(cv, x, y, z, rx, ry, rz, mix, seed=0, rough=0.9, force=False):
    nz = cv.noise
    for dx in range(-int(rx) - 1, int(rx) + 2):
        for dy in range(-int(ry) - 1, int(ry) + 2):
            for dz in range(-int(rz) - 1, int(rz) + 2):
                d = math.sqrt((dx / rx) ** 2 + (dy / ry) ** 2 + (dz / rz) ** 2)
                if d + (nz.n3(x + dx + seed, y + dy - seed, z + dz, 2.0) - 0.5) * rough < 1.0:
                    if force or cv.empty(x + dx, y + dy, z + dz):
                        cv.set(x + dx, y + dy, z + dz, LEAF(cv.pick(mix)))

def trunk_line(cv, x0, y0, z0, x1, y1, z1, log, thick=1):
    n = int(max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))) + 1
    for i in range(n + 1):
        t = i / max(1, n)
        x = round(x0 + (x1 - x0) * t); y = round(y0 + (y1 - y0) * t); z = round(z0 + (z1 - z0) * t)
        for a in range(thick):
            for b in range(thick):
                cv.set(x + a, y, z + b, log)

def oak(cv, x, y, z, h=5, log='oak_log', leaves='oak_leaves', r=2.6, seed=0):
    for i in range(h): cv.set(x, y + i, z, log)
    blob(cv, x, y + h, z, r, r * 0.75, r, [leaves], seed)
    cv.set(x, y + h - 1, z, log)

def big_oak(cv, x, y, z, h=10, log='oak_log', leaves='oak_leaves', r=5.0, seed=0, extra=None):
    """2x2 trunk, a few branches, several canopy blobs"""
    for i in range(h):
        for a in (0, 1):
            for b in (0, 1): cv.set(x + a, y + i, z + b, log)
    rng = cv.rng
    for k in range(4):
        ang = k * math.pi / 2 + rng.random() * 0.8; L = r * 0.8
        bx = x + round(math.cos(ang) * L); bz = z + round(math.sin(ang) * L); by = y + h - 2 + rng.randint(-1, 2)
        trunk_line(cv, x, y + h - 4, z, bx, by, bz, log.replace('[axis=y]', ''))
        blob(cv, bx, by + 1, bz, r * 0.62, r * 0.45, r * 0.62, [leaves] + (extra or []), seed + k)
    blob(cv, x, y + h + 1, z, r * 0.8, r * 0.55, r * 0.8, [leaves] + (extra or []), seed + 9)
    # roots
    for dx, dz in ((-1, 0), (2, 1), (1, -1), (0, 2)):
        cv.set(x + dx, y, z + dz, log)

def spruce(cv, x, y, z, h=9, log='spruce_log', leaves='spruce_leaves', r=3, snow=False):
    for i in range(h): cv.set(x, y + i, z, log)
    top = y + h
    layer = 0
    for yy in range(top, y + 2, -1):
        rr = min(r, (top - yy) // 2 + 1) - (1 if (top - yy) % 2 else 0) * (1 if (top - yy) > 2 else 0)
        rr = max(0, rr)
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) + abs(dz) <= rr + (1 if rr > 1 else 0) and cv.empty(x + dx, yy, z + dz):
                    cv.set(x + dx, yy, z + dz, LEAF(leaves))
                    if snow and cv.empty(x + dx, yy + 1, z + dz) and cv.rng.random() < 0.6:
                        cv.set(x + dx, yy + 1, z + dz, 'snow[layers=1]')
    cv.set(x, top, z, LEAF(leaves)); cv.set(x, top + 1, z, LEAF(leaves))

def cherry(cv, x, y, z, h=5, r=4.0, seed=0):
    for i in range(h): cv.set(x, y + i, z, 'cherry_log')
    # two leaning branches
    for k, (ax, az) in enumerate(((1, 0), (-1, 1), (0, -1))):
        bx, bz = x + ax * 2, z + az * 2
        trunk_line(cv, x, y + h - 2, z, bx, y + h, bz, 'cherry_wood')
        blob(cv, bx, y + h + 1, bz, r * 0.75, r * 0.4, r * 0.75, ['cherry_leaves'], seed + k, rough=1.1)
    blob(cv, x, y + h + 1, z, r, r * 0.45, r, ['cherry_leaves'], seed + 7, rough=1.1)
    # drooping petals
    for _ in range(int(r * 5)):
        dx = cv.rng.randint(-int(r), int(r)); dz = cv.rng.randint(-int(r), int(r))
        yy = y + h + 3
        while yy > y and cv.empty(x + dx, yy, z + dz): yy -= 1
        if cv.get(x + dx, yy, z + dz) and 'leaves' in cv.get(x + dx, yy, z + dz) and cv.rng.random() < 0.5:
            for i in range(1, cv.rng.randint(1, 3)):
                if cv.empty(x + dx, yy - i, z + dz): cv.set(x + dx, yy - i, z + dz, LEAF('cherry_leaves'))

def palm(cv, x, y, z, h=7, lean=(1, 0), seed=0):
    px, pz = x, z
    for i in range(h):
        if i > 2 and i % 3 == 0: px += lean[0]; pz += lean[1]
        cv.set(px, y + i, pz, 'jungle_log')
    ty = y + h
    cv.set(px, ty, pz, LEAF('jungle_leaves'))
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        L = 4 if dx and dz else 5
        for i in range(1, L):
            yy = ty - (1 if i >= L - 1 else 0)
            fx = px + round(dx * i * (0.75 if dx and dz else 1)); fz = pz + round(dz * i * (0.75 if dx and dz else 1))
            cv.set(fx, yy, fz, LEAF('jungle_leaves'))
    cv.set(px + 1, ty - 1, pz, 'cocoa[age=2,facing=west]')

def mushroom(cv, x, y, z, h=7, r=4, kind='red'):
    for i in range(h): cv.set(x, y + i, z, 'mushroom_stem')
    cap = 'red_mushroom_block' if kind == 'red' else 'brown_mushroom_block'
    if kind == 'red':
        for dy in range(0, 3):
            rr = r - (0 if dy < 2 else 1)
            for dx in range(-rr, rr + 1):
                for dz in range(-rr, rr + 1):
                    d = math.hypot(dx, dz)
                    if d <= rr + 0.3 and (dy == 2 or d >= rr - 0.9):
                        cv.set(x + dx, y + h - 1 + dy, z + dz, cap)
    else:
        for dx in range(-r - 1, r + 2):
            for dz in range(-r - 1, r + 2):
                if math.hypot(dx, dz) <= r + 0.8: cv.set(x + dx, y + h, z + dz, cap)

def dead_tree(cv, x, y, z, h=6, log='dark_oak_log'):
    for i in range(h): cv.set(x, y + i, z, log)
    for (dx, dz, dy) in ((1, 0, 3), (-1, 1, 4), (0, -1, 5)):
        trunk_line(cv, x, y + dy, z, x + dx * 3, y + dy + 2, z + dz * 3, log)

def autumn_tree(cv, x, y, z, h=6, r=3.4, seed=0):
    oak(cv, x, y, z, h, 'birch_log' if seed % 3 == 0 else 'oak_log', 'oak_leaves', 0.1)
    blob(cv, x, y + h, z, r, r * 0.8, r, [('orange_terracotta', 3), ('red_terracotta', 2), ('yellow_terracotta', 2), ('orange_wool', 2), ('red_wool', 1)], seed)

def crystal(cv, x, y, z, h=5, mats=('amethyst_block',), tip='amethyst_cluster[facing=up]', lean=(0, 0)):
    for i in range(h):
        w = 1 if i < h - 2 else 0
        cx = x + round(lean[0] * i / h); cz = z + round(lean[1] * i / h)
        cv.set(cx, y + i, cz, cv.pick(list(mats)))
        if w and i < h // 2:
            for dx, dz in ((1, 0), (0, 1)): cv.set(cx + dx, y + i, cz + dz, cv.pick(list(mats)))
    cv.set(x + round(lean[0]), y + h, z + round(lean[1]), tip)

# ------------------------------------------------------------------ small structures
def lantern_post(cv, x, y, z, post='spruce_fence', lamp='lantern', h=3):
    for i in range(h): cv.set(x, y + i, z, post)
    cv.set(x, y + h, z, lamp + '[hanging=false]' if lamp.endswith('lantern') and lamp != 'sea_lantern' else lamp)

def path(cv, hm, pts, w, mix, th=None):
    """a winding path through hm along polyline pts"""
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(z1 - z0))) + 1
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n); z = round(z0 + (z1 - z0) * i / n)
            for dx in range(-w, w + 1):
                for dz in range(-w, w + 1):
                    if abs(dx) + abs(dz) <= w and (x + dx, z + dz) in hm and cv.rng.random() < 0.9:
                        y = hm[(x + dx, z + dz)]; cv.set(x + dx, y, z + dz, cv.pick(mix))
                        if cv.get(x + dx, y + 1, z + dz) and 'leaves' not in cv.get(x + dx, y + 1, z + dz) and 'log' not in cv.get(x + dx, y + 1, z + dz):
                            cv.set(x + dx, y + 1, z + dz, None)

def roof_gable(cv, x0, x1, z0, z1, y, mat_stair, mat_full, trim=None, axis='x'):
    """gable roof over [x0,x1]x[z0,z1] starting at height y, ridge along axis"""
    if axis == 'x':
        half = (z1 - z0) // 2 + 1
        for i in range(half + 1):
            for x in range(x0 - 1, x1 + 2):
                za, zb = z0 - 1 + i, z1 + 1 - i
                if za > zb: continue
                if za == zb:
                    cv.set(x, y + i, za, mat_full if not trim else trim)
                else:
                    cv.set(x, y + i, za, f'{mat_stair}[facing=south,half=bottom]')
                    cv.set(x, y + i, zb, f'{mat_stair}[facing=north,half=bottom]')
            # gable walls
            for z in range(z0 - 1 + i + 1, z1 + 1 - i):
                for x in (x0, x1):
                    if i > 0: cv.set(x, y + i - 1, z, mat_full)
        if trim:
            for x in range(x0 - 1, x1 + 2):
                cv.set(x, y + half, z0 + (z1 - z0) // 2, trim) if (z1 - z0) % 2 == 0 else None
    else:
        half = (x1 - x0) // 2 + 1
        for i in range(half + 1):
            for z in range(z0 - 1, z1 + 2):
                xa, xb = x0 - 1 + i, x1 + 1 - i
                if xa > xb: continue
                if xa == xb:
                    cv.set(xa, y + i, z, mat_full if not trim else trim)
                else:
                    cv.set(xa, y + i, z, f'{mat_stair}[facing=east,half=bottom]')
                    cv.set(xb, y + i, z, f'{mat_stair}[facing=west,half=bottom]')
            for x in range(x0 - 1 + i + 1, x1 + 1 - i):
                for z in (z0, z1):
                    if i > 0: cv.set(x, y + i - 1, z, mat_full)

def roof_hip(cv, x0, x1, z0, z1, y, mat_stair, cap):
    """pyramid roof"""
    i = 0
    while x0 - 1 + i <= x1 + 1 - i and z0 - 1 + i <= z1 + 1 - i:
        xa, xb, za, zb = x0 - 1 + i, x1 + 1 - i, z0 - 1 + i, z1 + 1 - i
        if xa == xb or za == zb:
            for x in range(xa, xb + 1):
                for z in range(za, zb + 1): cv.set(x, y + i, z, cap)
            break
        for x in range(xa, xb + 1):
            cv.set(x, y + i, za, f'{mat_stair}[facing=south,half=bottom]'); cv.set(x, y + i, zb, f'{mat_stair}[facing=north,half=bottom]')
        for z in range(za + 1, zb):
            cv.set(xa, y + i, z, f'{mat_stair}[facing=east,half=bottom]'); cv.set(xb, y + i, z, f'{mat_stair}[facing=west,half=bottom]')
        for x in range(xa + 1, xb):
            for z in range(za + 1, zb): cv.set(x, y + i, z, None) if False else None
        i += 1
    return y + i

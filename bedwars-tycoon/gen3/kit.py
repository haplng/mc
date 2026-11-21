"""Building kit: geometric primitives, natural islands and trees, furniture, and the standard bed wars fixtures."""
import math
from canvas import Canvas, rot_xz

TEAMS = [('red', 'red'), ('blue', 'blue'), ('green', 'lime'), ('yellow', 'yellow'),
         ('aqua', 'cyan'), ('white', 'white'), ('pink', 'pink'), ('gray', 'gray')]

# ------------------------------------------------------------------ materials
def M(cv, s, x=0, y=0, z=0):
    """resolve a material spec: a state string, a weighted list, or a function (x, y, z) -> state"""
    if s is None or isinstance(s, str): return s
    if callable(s): return s(x, y, z)
    return cv.pick(s)

def put(cv, x, y, z, s, force=True):
    b = M(cv, s, x, y, z)
    if b is not None: cv.set(x, y, z, b, force)

def leaf(s): return s + '[persistent=true]' if 'leaves' in s and '[' not in s else s

def stair(mat, facing, half='bottom'): return f'{mat}_stairs[facing={facing},half={half}]'
def slab(mat, typ='bottom'): return f'{mat}_slab[type={typ}]'
def towards(dx, dz):
    """facing name for a horizontal direction"""
    if abs(dx) >= abs(dz): return 'east' if dx > 0 else 'west'
    return 'south' if dz > 0 else 'north'
OPP = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}

# ------------------------------------------------------------------ primitives
def box(cv, x0, y0, z0, x1, y1, z1, s, hollow=False, force=True):
    xa, xb = sorted((x0, x1)); ya, yb = sorted((y0, y1)); za, zb = sorted((z0, z1))
    for x in range(xa, xb + 1):
        for y in range(ya, yb + 1):
            for z in range(za, zb + 1):
                if hollow and xa < x < xb and ya < y < yb and za < z < zb: continue
                if s is None: cv.set(x, y, z, None)
                else: put(cv, x, y, z, s, force)

def clear(cv, x0, y0, z0, x1, y1, z1):
    xa, xb = sorted((x0, x1)); ya, yb = sorted((y0, y1)); za, zb = sorted((z0, z1))
    for x in range(xa, xb + 1):
        for y in range(ya, yb + 1):
            for z in range(za, zb + 1): cv.set(x, y, z, None)

def disc(cv, cx, y, cz, r, s, r_in=None, force=True):
    R = int(math.ceil(r)) + 1
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            d = math.hypot(dx, dz)
            if d < r + 0.5 and (r_in is None or d >= r_in + 0.5): put(cv, cx + dx, y, cz + dz, s, force)

def ring(cv, cx, y, cz, r, s, force=True):
    disc(cv, cx, y, cz, r, s, r_in=r - 1, force=force)

def cyl(cv, cx, y0, y1, cz, r, s, hollow=False, force=True):
    """vertical cylinder; r may be a function of y for tapered shapes"""
    for y in range(y0, y1 + 1):
        rr = r(y) if callable(r) else r
        disc(cv, cx, y, cz, rr, s, r_in=(rr - 1 if hollow else None), force=force)

def ellipsoid(cv, cx, cy, cz, rx, ry, rz, s, hollow=False, ymin=None, ymax=None, force=True):
    for dy in range(-int(ry) - 1, int(ry) + 2):
        y = cy + dy
        if (ymin is not None and y < ymin) or (ymax is not None and y > ymax): continue
        for dx in range(-int(rx) - 1, int(rx) + 2):
            for dz in range(-int(rz) - 1, int(rz) + 2):
                d = math.sqrt((dx / (rx + 0.5)) ** 2 + (dy / (ry + 0.5)) ** 2 + (dz / (rz + 0.5)) ** 2)
                if d >= 1: continue
                if hollow:
                    di = math.sqrt((dx / max(0.5, rx - 0.5)) ** 2 + (dy / max(0.5, ry - 0.5)) ** 2 + (dz / max(0.5, rz - 0.5)) ** 2)
                    if di < 1: continue
                put(cv, cx + dx, y, cz + dz, s, force)

def sphere(cv, cx, cy, cz, r, s, hollow=False, ymin=None, ymax=None, force=True):
    ellipsoid(cv, cx, cy, cz, r, r, r, s, hollow, ymin, ymax, force)

def cone(cv, cx, y0, cz, r, h, s, hollow=False, force=True):
    for i in range(h):
        rr = r * (1 - i / h)
        disc(cv, cx, y0 + i, cz, rr, s, r_in=(rr - 1 if hollow and rr >= 1 else None), force=force)

def torus(cv, cx, cy, cz, R, r, s, ry=None, force=True):
    ry = ry or r
    for dy in range(-int(ry) - 1, int(ry) + 2):
        for dx in range(-int(R + r) - 1, int(R + r) + 2):
            for dz in range(-int(R + r) - 1, int(R + r) + 2):
                q = math.hypot(dx, dz) - R
                if (q / (r + 0.5)) ** 2 + (dy / (ry + 0.5)) ** 2 < 1: put(cv, cx + dx, cy + dy, cz + dz, s, force)

def lathe(cv, cx, y0, cz, radii, s, hollow=False, force=True):
    """a turned shape: one radius per layer, bottom to top"""
    for i, rr in enumerate(radii):
        if rr is None: continue
        disc(cv, cx, y0 + i, cz, rr, s, r_in=(rr - 1 if hollow and rr >= 1.5 else None), force=force)

def line(cv, a, b, s, thick=0, force=True):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]), abs(b[2] - a[2])) * 1.5) + 1
    for i in range(n + 1):
        t = i / n
        x = a[0] + (b[0] - a[0]) * t; y = a[1] + (b[1] - a[1]) * t; z = a[2] + (b[2] - a[2]) * t
        if thick <= 0: put(cv, round(x), round(y), round(z), s, force)
        else: sphere(cv, round(x), round(y), round(z), thick, s, force=force)

def curve(cv, pts, s, thick=0, force=True, taper=None):
    """smooth curve through control points (Catmull-Rom); taper: (r_start, r_end) for tentacle-like shapes"""
    P = [pts[0]] + list(pts) + [pts[-1]]
    segs = len(P) - 3; total = 0
    for i in range(segs):
        p0, p1, p2, p3 = P[i:i + 4]
        n = int(max(abs(p2[k] - p1[k]) for k in range(3)) * 2) + 2
        for j in range(n + 1):
            t = j / n; t2 = t * t; t3 = t2 * t
            q = [0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in range(3)]
            f = (i + t) / segs
            rr = thick if taper is None else taper[0] + (taper[1] - taper[0]) * f
            if rr <= 0.4: put(cv, round(q[0]), round(q[1]), round(q[2]), s, force)
            else: sphere(cv, round(q[0]), round(q[1]), round(q[2]), rr, s, force=force)

def vdisc(cv, cx, cy, cz, r, s, axis='x', r_in=None, force=True):
    """a disc standing upright: axis is the direction it faces ('x' -> lies in the y-z plane)"""
    R = int(math.ceil(r)) + 1
    for da in range(-R, R + 1):
        for dy in range(-R, R + 1):
            d = math.hypot(da, dy)
            if d < r + 0.5 and (r_in is None or d >= r_in + 0.5):
                if axis == 'x': put(cv, cx, cy + dy, cz + da, s, force)
                else: put(cv, cx + da, cy + dy, cz, s, force)

# ------------------------------------------------------------------ patterns
def checker(a, b, size=1, ox=0, oz=0):
    return lambda x, y, z: a if (((x - ox) // size) + ((z - oz) // size)) % 2 == 0 else b

def sectors(cx, cz, n, mats):
    """material by angle sector round (cx, cz): n sectors cycling through mats"""
    def f(x, y, z):
        a = (math.atan2(z - cz, x - cx) + 2 * math.pi) % (2 * math.pi)
        return mats[int(a / (2 * math.pi) * n) % len(mats)]
    return f

def bands(mats, h=1, oy=0):
    return lambda x, y, z: mats[((y - oy) // h) % len(mats)]

# ------------------------------------------------------------------ natural islands
def squircle(hx, hz, n=4.0):
    return lambda dx, dz: (abs(dx / hx) ** n + abs(dz / hz) ** n) ** (1.0 / n)

def island(cv, cx, cy, cz, shape, depth, th, seed, flat=0.0, hill=1.5, rough=0.2, ext=None, top=None, spikes=True):
    """Organic floating island. shape: (rx, rz) ellipse or a function (dx, dz) -> 0 (centre) .. 1 (edge).
    Flat top at cy inside `flat`, gentle hills further out, layered rock below that narrows to hanging tips.
    Returns {(x, z): top_y}."""
    nz = cv.noise; hm = {}; so = seed * 131.7
    if callable(shape):
        fn = shape; ex, ez = ext
    else:
        rx, rz = shape; fn = lambda dx, dz: math.sqrt((dx / rx) ** 2 + (dz / rz) ** 2); ex, ez = rx, rz
    strata = th.get('strata') or [s for s, w in th['under'] for _ in range(max(1, int(w)))]
    sub_n = th.get('sub_n', 3)
    for x in range(int(cx - ex - 4), int(cx + ex + 5)):
        for z in range(int(cz - ez - 4), int(cz + ez + 5)):
            d = fn(x - cx, z - cz)
            d2 = d + (nz.f2(x + so, z - so, 9.0) - 0.5) * rough * 2.2
            if d2 >= 1.0: continue
            core = d2 < flat
            bump = 0 if core else int(round((nz.f2(x - so, z + so, 6.0) - 0.42) * 2 * hill * min(1.0, (d2 - flat) / 0.25 + 0.2)))
            if d2 > 0.93: bump = min(bump, 0)
            ty = cy + max(-1, bump)
            smooth = nz.f2(x * 0.9 + so, z * 0.9 - so, 7.0, 3)
            dep = depth * (1 - min(1.0, max(0.0, d2))) ** 0.55 * (0.7 + 0.6 * smooth) + 2
            if spikes:
                sp = nz.n2(x * 3.1 - so, z * 3.1 + so, 2.0)
                if sp > 0.78 and d2 < 0.85: dep += (sp - 0.78) * 30 * (1 - d2)
            by = int(cy - dep)
            for y in range(by, ty + 1):
                if y == ty: b = M(cv, top or th['top'], x, y, z)
                elif ty - y <= sub_n: b = cv.pick(th['sub'])
                elif y - by <= 1: b = cv.pick(th['tip'])
                else:
                    band = int((y + nz.n2(x * 0.7, z * 0.7 + y * 0.1, 5.0) * 5) // 3)
                    b = strata[band % len(strata)] if cv.rng.random() < 0.85 else cv.pick(th['under'])
                cv.set(x, y, z, b)
            hm[(x, z)] = ty
            h = th.get('hang')
            if h and d2 > 0.5 and cv.rng.random() < h.get('p', 0.1):
                ln = cv.rng.randint(1, h.get('max', 3))
                for i in range(1, ln + 1):
                    if not cv.empty(x, by - i, z): break
                    cv.set(x, by - i, z, h['body'] if i < ln else h['end'])
    return hm

def flatten(cv, hm, x0, z0, x1, z1, y, th, top=None):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x, z) not in hm: continue
            ty = hm[(x, z)]
            for yy in range(y + 1, ty + 4): cv.set(x, yy, z, None)
            for yy in range(min(ty, y), y):
                if cv.empty(x, yy, z): cv.set(x, yy, z, cv.pick(th['sub']))
            put(cv, x, y, z, top or th['top']); hm[(x, z)] = y

def flora(cv, hm, plants, density=0.18, on=('grass_block', 'moss_block', 'podzol', 'dirt', 'coarse_dirt'), avoid=None):
    """scatter plants on the island top. A plant ending in '|tall' is a two-block plant."""
    for (x, z), y in hm.items():
        if avoid and avoid(x, z): continue
        if not cv.empty(x, y + 1, z) or cv.name(x, y, z) not in on: continue
        if cv.rng.random() < density:
            s = cv.pick(plants)
            if s.endswith('|tall'):
                if cv.empty(x, y + 2, z):
                    cv.set(x, y + 1, z, s[:-5] + '[half=lower]'); cv.set(x, y + 2, z, s[:-5] + '[half=upper]')
            else: cv.set(x, y + 1, z, s)

# ------------------------------------------------------------------ trees and rocks
def blob(cv, x, y, z, rx, ry, rz, mix, seed=0, rough=0.9, force=False):
    nz = cv.noise
    for dx in range(-int(rx) - 1, int(rx) + 2):
        for dy in range(-int(ry) - 1, int(ry) + 2):
            for dz in range(-int(rz) - 1, int(rz) + 2):
                d = math.sqrt((dx / rx) ** 2 + (dy / ry) ** 2 + (dz / rz) ** 2)
                if d + (nz.n3(x + dx + seed, y + dy - seed, z + dz, 2.0) - 0.5) * rough < 1.0:
                    if force or cv.empty(x + dx, y + dy, z + dz): cv.set(x + dx, y + dy, z + dz, leaf(M(cv, mix, x + dx, y + dy, z + dz)))

def boulder(cv, x, y, z, r, mix, seed=0, squash=0.8):
    nz = cv.noise; R = int(math.ceil(r)) + 1
    for dx in range(-R, R + 1):
        for dy in range(-R, R + 1):
            for dz in range(-R, R + 1):
                d = math.sqrt(dx * dx + (dy / squash) ** 2 + dz * dz)
                if d + (nz.n3(x + dx + seed, y + dy, z + dz, 2.5) - 0.5) * 1.6 < r: put(cv, x + dx, y + dy, z + dz, mix)

def oak(cv, x, y, z, h=5, log='oak_log', leaves='oak_leaves', r=2.6, seed=0):
    for i in range(h): cv.set(x, y + i, z, log)
    blob(cv, x, y + h, z, r, r * 0.75, r, [leaves], seed)

def big_tree(cv, x, y, z, h=10, log='oak_log', leaves='oak_leaves', r=5.0, seed=0):
    for i in range(h):
        for a in (0, 1):
            for b in (0, 1): cv.set(x + a, y + i, z + b, log)
    for k in range(4):
        ang = k * math.pi / 2 + cv.rng.random() * 0.8; L = r * 0.8
        bx = x + round(math.cos(ang) * L); bz = z + round(math.sin(ang) * L); by = y + h - 2 + cv.rng.randint(-1, 2)
        line(cv, (x, y + h - 4, z), (bx, by, bz), log)
        blob(cv, bx, by + 1, bz, r * 0.62, r * 0.45, r * 0.62, [leaves], seed + k)
    blob(cv, x, y + h + 1, z, r * 0.8, r * 0.55, r * 0.8, [leaves], seed + 9)
    for dx, dz in ((-1, 0), (2, 1), (1, -1), (0, 2)): cv.set(x + dx, y, z + dz, log)

def spruce(cv, x, y, z, h=9, log='spruce_log', leaves='spruce_leaves', r=3):
    for i in range(h): cv.set(x, y + i, z, log)
    top = y + h
    for yy in range(top, y + 2, -1):
        rr = max(0, min(r, (top - yy) // 2 + 1) - (1 if (top - yy) % 2 and (top - yy) > 2 else 0))
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) + abs(dz) <= rr + (1 if rr > 1 else 0) and cv.empty(x + dx, yy, z + dz): cv.set(x + dx, yy, z + dz, leaf(leaves))
    cv.set(x, top, z, leaf(leaves)); cv.set(x, top + 1, z, leaf(leaves))

def palm(cv, x, y, z, h=7, lean=(1, 0), log='jungle_log', leaves='jungle_leaves'):
    px, pz = x, z
    for i in range(h):
        if i > 2 and i % 3 == 0: px += lean[0]; pz += lean[1]
        cv.set(px, y + i, pz, log)
    ty = y + h; cv.set(px, ty, pz, leaf(leaves))
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        diag = dx != 0 and dz != 0; L = 4 if diag else 5
        for i in range(1, L):
            yy = ty - (1 if i >= L - 1 else 0)
            f = 0.75 if diag else 1
            cv.set(px + round(dx * i * f), yy, pz + round(dz * i * f), leaf(leaves), force=False)
    return px, ty, pz

def cherry(cv, x, y, z, h=5, r=4.0, seed=0):
    for i in range(h): cv.set(x, y + i, z, 'cherry_log')
    for k, (ax, az) in enumerate(((1, 0), (-1, 1), (0, -1))):
        bx, bz = x + ax * 2, z + az * 2
        line(cv, (x, y + h - 2, z), (bx, y + h, bz), 'cherry_wood')
        blob(cv, bx, y + h + 1, bz, r * 0.75, r * 0.4, r * 0.75, ['cherry_leaves'], seed + k, rough=1.1)
    blob(cv, x, y + h + 1, z, r, r * 0.45, r, ['cherry_leaves'], seed + 7, rough=1.1)

# ------------------------------------------------------------------ small props
def post_lamp(cv, x, y, z, post='spruce_fence', lamp='lantern', h=3):
    for i in range(h): cv.set(x, y + i, z, post)
    cv.set(x, y + h, z, lamp + '[hanging=false]' if lamp in ('lantern', 'soul_lantern', 'copper_lantern') else lamp)

def hang_lamp(cv, x, y, z, lamp='lantern', chain=0):
    """a lantern hanging below (x, y+1+chain, z), which must be a solid block"""
    for i in range(chain): cv.set(x, y + 1 + i, z, 'iron_chain[axis=y]')
    cv.set(x, y, z, lamp + '[hanging=true]')

def table(cv, x, y, z, wood='oak', chairs=((0, 1), (0, -1))):
    cv.set(x, y, z, f'{wood}_fence'); cv.set(x, y + 1, z, f'{wood}_pressure_plate')
    for dx, dz in chairs:
        cv.set(x + dx, y, z + dz, stair(wood, towards(dx, dz)))

def rug(cv, x0, z0, x1, z1, y, inner, edge=None):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            border = x in (x0, x1) or z in (z0, z1)
            if cv.empty(x, y, z) and not cv.empty(x, y - 1, z): cv.set(x, y, z, f'{edge if (border and edge) else inner}_carpet')

def crates(cv, x, y, z, n=3, kinds=('barrel[facing=up]', 'barrel[facing=up]', 'spruce_planks', 'composter')):
    """a little pile of barrels and boxes"""
    spots = [(0, 0, 0), (1, 0, 0), (0, 0, 1), (0, 1, 0), (1, 0, 1)]
    for i in range(min(n, len(spots))):
        dx, dy, dz = spots[i]
        if cv.empty(x + dx, y + dy, z + dz): cv.set(x + dx, y + dy, z + dz, cv.rng.choice(kinds))

# ------------------------------------------------------------------ bed wars fixtures
def bed(cv, dye, x, y, z, facing='south'):
    """foot at (x, y, z), head one block further in `facing`"""
    dx, dz = {'south': (0, 1), 'north': (0, -1), 'east': (1, 0), 'west': (-1, 0)}[facing]
    cv.set(x, y, z, f'{dye}_bed[facing={facing},part=foot]'); cv.set(x + dx, y, z + dz, f'{dye}_bed[facing={facing},part=head]')

def gen_pad(cv, x, y, z, kind, frame='polished_andesite', corner=None):
    """a flush 3x3 generator pad (kind: iron / diamond / emerald)"""
    core = {'iron': 'iron_block', 'diamond': 'diamond_block', 'emerald': 'emerald_block'}[kind]
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if dx == 0 and dz == 0: b = core
            elif dx == 0 or dz == 0: b = 'gold_block' if kind == 'iron' else frame
            else: b = corner or frame
            put(cv, x + dx, y, z + dz, b)
            for yy in (1, 2, 3): cv.set(x + dx, y + yy, z + dz, None)

def gen_shrine(cv, x, y, z, kind, post, roof_slab, h=4, lamp=None):
    """four posts round a generator pad carrying a small roof with the gem set into it"""
    gem = {'iron': 'iron_block', 'diamond': 'diamond_block', 'emerald': 'emerald_block'}[kind]
    for dx in (-2, 2):
        for dz in (-2, 2):
            for i in range(1, h + 1): put(cv, x + dx, y + i, z + dz, post)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            put(cv, x + dx, y + h + 1, z + dz, gem if (dx, dz) == (0, 0) else roof_slab)
    if lamp: cv.set(x, y + h, z, lamp)

def team_markers(cv, dye, spawn, bedpos, gen, shop, upg):
    tags = ['bw', 'bw.team', 'bw.t.' + dye]
    cv.marker(*spawn, tags + ['bw.spawn']); cv.marker(*bedpos, tags + ['bw.bed'])
    cv.marker(gen[0], gen[1] + 1, gen[2], tags + ['bw.gen', 'bw.gen.iron'])
    cv.marker(*shop, tags + ['bw.shop']); cv.marker(*upg, tags + ['bw.upgrade'])

def gem_marker(cv, x, y, z, kind):
    cv.marker(x, y + 1, z, ['bw', 'bw.gen', 'bw.gen.' + kind])

# ------------------------------------------------------------------ map assembly
class MapBuilder:
    """Places islands on a map and remembers their outlines so that the gaps between them can be measured."""
    def __init__(self, seed=1):
        self.cv = Canvas(seed); self.parts = []; self.overlap = 0

    def put(self, obj, x, z, y=0, k=0, flip=False, kind='extra'):
        self.overlap += self.cv.paste(obj, x, y, z, k, flip)
        fp = set()
        for (px, pz) in obj.footprint():
            if flip: px = -px
            rx, rz = rot_xz(px, pz, k); fp.add((rx + x, rz + z))
        self.parts.append((kind, fp))

    def bases(self, fn, R, delta, y=0, teams=TEAMS):
        """eight bases as four mirrored pairs. Side q faces the centre line; the pair sits at +-delta degrees off the side's axis."""
        i = 0
        for q in range(4):
            for sgn in (-1, 1):
                a = math.radians(90 * q + sgn * delta)
                x, z = round(R * math.cos(a)), round(R * math.sin(a))
                self.put(fn(teams[i][1]), x, z, y, (q + 1) % 4, flip=(sgn > 0), kind='base'); i += 1

    def bases_at(self, fn, spots, y=0, teams=TEAMS):
        """spots: list of (x, z, k, flip)"""
        for i, (x, z, k, flip) in enumerate(spots):
            self.put(fn(teams[i][1]), x, z, y, k, flip, kind='base')

    def around(self, fn, R, angles_deg, y=0, kind='extra', face_in=True):
        """one object per angle; fn(i) -> canvas whose +z is its front. Fronts are turned towards the centre (nearest quarter turn)."""
        for i, deg in enumerate(angles_deg):
            a = math.radians(deg); x, z = round(R * math.cos(a)), round(R * math.sin(a))
            k = 0
            if face_in:
                best = None
                for kk in range(4):
                    fx, fz = rot_xz(0, 1, kk); dot = fx * -math.cos(a) + fz * -math.sin(a)
                    if best is None or dot > best[0] + 1e-9: best = (dot, kk)
                k = best[1]
            self.put(fn(i), x, z, y, k, kind=kind)

    def gaps(self):
        import numpy as np
        from scipy.spatial import cKDTree
        arrs = [(k, np.array(sorted(fp))) for k, fp in self.parts if fp]
        trees = [cKDTree(a) for _, a in arrs]
        res = {}
        for i in range(len(arrs)):
            for j in range(i + 1, len(arrs)):
                d = float(trees[j].query(arrs[i][1], k=1)[0].min())
                key = '-'.join(sorted((arrs[i][0], arrs[j][0])))
                res[key] = min(res.get(key, 1e9), d)
        return {k: round(v) for k, v in sorted(res.items())}

# ------------------------------------------------------------------ more helpers
def xs(s, k=0, flip=False):
    from canvas import xform_state
    return xform_state(s, k, flip)

def under_steps(cv, x0, z0, x1, z1, y, n, mats, inset=2):
    """an upside-down stepped pyramid below a rectangular platform (first layer directly under y)"""
    for i in range(n):
        a, b, c, d = x0 + inset * i, z0 + inset * i, x1 - inset * i, z1 - inset * i
        if a > c or b > d: break
        box(cv, a, y - 1 - i, b, c, y - 1 - i, d, mats[i % len(mats)])

def under_dome(cv, cx, y, cz, r, depth, mats):
    """a rounded bowl below a round platform; mats: one material spec per layer (cycled)"""
    for i in range(1, depth + 1):
        rr = r * math.sqrt(max(0.0, 1 - (i / (depth + 0.5)) ** 2))
        if rr < 0.6: break
        disc(cv, cx, y - i, cz, rr, mats[(i - 1) % len(mats)])

def stall(cv, x, y, z, k=0, a='white', b='red', counter='barrel[facing=up]', post='spruce_fence'):
    """a little market stall behind the spot (x, y, z) where a shopkeeper will stand; its open side looks towards local +z"""
    t = Canvas(1)
    for dx in (-1, 0, 1): t.set(dx, 0, -1, counter)
    for dx in (-1, 1):
        t.set(dx, 1, -1, post); t.set(dx, 2, -1, post)
    for dx in (-1, 0, 1):
        for dz in (-1, 0): t.set(dx, 3, dz, (b if dx == 0 else a) + '_wool')
    t.set(0, 1, -1, 'lantern[hanging=false]')
    cv.paste(t, x, y, z, k)

def flag(cv, x, y, z, h, dye, d=(1, 0), pole='oak_fence', w=3, hh=2):
    """a pole of height h with a wool flag at its top flying in direction d"""
    for i in range(h): cv.set(x, y + i, z, pole)
    for i in range(1, w + 1):
        for j in range(hh): cv.set(x + d[0] * i, y + h - 1 - j, z + d[1] * i, dye + '_wool')

PIECES = {'pawn': [2.2, 1.7, 1.1, 1.0, 1.0, 1.6, 1.0], 'rook': [2.2, 2.2, 1.6, 1.5, 1.5, 1.5, 1.5, 2.0, 2.2],
          'bishop': [2.2, 1.9, 1.3, 1.0, 1.0, 1.0, 1.5, 1.0, 1.5, 1.8, 1.6, 1.2, 0.7],
          'queen': [2.4, 2.1, 1.5, 1.2, 1.1, 1.1, 1.1, 1.6, 1.1, 1.3, 1.7, 2.1, 2.3],
          'king': [2.4, 2.1, 1.5, 1.2, 1.2, 1.2, 1.2, 1.7, 1.2, 1.4, 1.8, 2.2, 1.6]}
def chess_piece(cv, x, y, z, kind, mat, f=1.0, trim=None):
    """a lathe-turned chess piece standing on (x, y, z); returns its top y"""
    if kind == 'knight':
        lathe(cv, x, y, z, [2.2 * f, 1.8 * f], mat)
        n = max(1, round(f))
        for i in range(6):
            sh = (-1, -1, 0, 0, 0, 1)[i]
            box(cv, x - n, y + 2 + i, z - 1 + sh, x + n, y + 2 + i, z + 1 + sh, mat)
        box(cv, x - n, y + 6, z, x + n, y + 8, z + 3, mat); box(cv, x - n, y + 6, z + 3, x + n, y + 6, z + 4, mat)
        cv.set(x - n, y + 9, z, mat); cv.set(x + n, y + 9, z, mat)
        for i in range(2, 9): cv.set(x, y + i, z - 2 + (0 if i < 5 else 1), trim or mat)
        return y + 9
    prof = PIECES[kind]; h = max(2, round(len(prof) * f))
    for i in range(h):
        r = prof[min(len(prof) - 1, int(i / f))] * f
        disc(cv, x, y + i, z, r, trim if (trim and prof[min(len(prof) - 1, int(i / f))] in (1.6, 1.5, 1.7) and i > 2) else mat)
    t = y + h
    if kind == 'pawn': sphere(cv, x, t + round(1.0 * f), z, 1.5 * f, mat); return t + round(2.5 * f)
    if kind == 'rook':
        r = round(2.2 * f)
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if max(abs(dx), abs(dz)) == r and (dx + dz) % 2 == 0 and math.hypot(dx, dz) < 2.2 * f + 0.9: cv.set(x + dx, t, z + dz, mat)
        return t
    if kind == 'bishop': cv.set(x, t, z, trim or mat); return t
    if kind == 'queen':
        r = 2.3 * f
        for a in range(0, 360, 45): cv.set(x + round(r * math.cos(math.radians(a))), t, z + round(r * math.sin(math.radians(a))), trim or mat)
        sphere(cv, x, t + 1, z, 1.2 * f, mat); cv.set(x, t + 2 + int(f), z, trim or mat); return t + 2 + int(f)
    if kind == 'king':
        n = max(1, round(f))
        for i in range(3 * n): cv.set(x, t + i, z, trim or mat)
        for d in range(-n, n + 1): cv.set(x + d, t + 2 * n - 1, z, trim or mat)
        return t + 3 * n
    return t

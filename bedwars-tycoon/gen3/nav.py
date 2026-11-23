"""Paths for the computer-controlled players, worked out from the built maps before the game ever runs.
For every map: the places a bot goes (its forge, its shop, each bed, each diamond and emerald generator), the way between any two
of them as a short list of points to walk to, and the blocks a team stacks round its bed.
A way may cross the void (the bot lays wool as it walks), climb one block (it jumps), drop up to three, or go straight up (it towers)."""
import sys, os, math, heapq, pickle, json, hashlib, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check
from util import TEAMS

WALK, DIAG, UP, DROP, BRIDGE, TOWER = 1.0, 1.42, 1.8, 1.3, 5.0, 8.0
CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

class _CV:
    def __init__(self): self.b = {}
_cache_open = {}; _cache_floor = {}
def is_open(state):
    """a bot can stand in this cell"""
    if state is None: return True
    n = check.nm(state)
    v = _cache_open.get(n)
    if v is None:
        cv = _CV(); cv.b[(0, 0, 0)] = state
        v = _cache_open[n] = check._open(cv, (0, 0, 0)) and n not in ('ladder', 'lava', 'cobweb', 'sweet_berry_bush', 'fire', 'water')
    return v
def is_floor(state):
    """a bot can stand on this cell (fences, walls and gates are too high to step on to)"""
    if state is None: return False
    n = check.nm(state)
    v = _cache_floor.get(n)
    if v is None:
        cv = _CV(); cv.b[(0, 0, 0)] = state
        v = _cache_floor[n] = (check._floor(cv, (0, 0, 0)) and not n.endswith(('_fence', '_wall', '_fence_gate', '_door', '_trapdoor', '_pane', '_bars', 'chain', 'lantern'))
                               and 'chest' not in n and n not in ('water', 'iron_bars', 'cactus', 'campfire', 'ladder', 'lava', 'cobweb', 'fire'))
    return v

class Grid:
    def __init__(self, b, pad=2, ylo=None, yhi=None):
        xs = [p[0] for p in b]; ys = [p[1] for p in b]; zs = [p[2] for p in b]
        self.x0, self.y0, self.z0 = min(xs) - pad, min(ys) - 1, min(zs) - pad
        self.sx, self.sy, self.sz = max(xs) + pad - self.x0 + 1, max(ys) + 6 - self.y0 + 1, max(zs) + pad - self.z0 + 1
        n = self.sx * self.sy * self.sz
        self.dx, self.dy, self.dz = self.sy * self.sz, self.sz, 1
        op = bytearray(b'\x01') * n; fl = bytearray(n)
        for (x, y, z), s in b.items():
            i = self.idx(x, y, z)
            if not is_open(s): op[i] = 0
            if is_floor(s): fl[i] = 1
        # the rim of the grid is closed, so a search never leaves it
        for x in range(self.sx):
            for y in range(self.sy):
                for z in range(self.sz):
                    if x in (0, self.sx - 1) or z in (0, self.sz - 1) or y in (0, self.sy - 1, self.sy - 2): op[(x * self.sy + y) * self.sz + z] = 0
        self.op = op; self.fl = fl
        self.ylo = ylo; self.yhi = yhi
    def idx(self, x, y, z): return ((x - self.x0) * self.sy + (y - self.y0)) * self.sz + (z - self.z0)
    def pos(self, i):
        z = i % self.sz; i //= self.sz; y = i % self.sy; x = i // self.sy
        return (x + self.x0, y + self.y0, z + self.z0)
    def node(self, i): return self.op[i] and self.op[i + self.dy]
    def ground(self, i): return self.fl[i - self.dy]
    def stand(self, x, y, z):
        i = self.idx(x, y, z); return bool(self.node(i) and self.ground(i))

def dijkstra(g, src, targets, limit=None):
    """cheapest ways from src to every target; returns {target: [cells]}"""
    op, fl, dx, dy, dz = g.op, g.fl, g.dx, g.dy, g.dz
    blo = g.idx(0, g.ylo, 0) // g.sz % g.sy; bhi = g.idx(0, g.yhi, 0) // g.sz % g.sy
    s = g.idx(*src); want = {g.idx(*t) for t in targets}
    dist = {s: 0.0}; par = {s: -1}; pq = [(0.0, s)]; left = set(want)
    card = ((dx, 0), (-dx, 0), (dz, 0), (-dz, 0))
    diag = ((dx + dz, dx, dz), (dx - dz, dx, -dz), (-dx + dz, -dx, dz), (-dx - dz, -dx, -dz))
    while pq and left:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18): continue
        if u in left:
            left.discard(u)
            if not left: break
        if limit and d > limit: break
        ug = fl[u - dy]; uy = u // g.sz % g.sy
        out = []
        for stp, _ in card:
            v = u + stp
            if op[v] and op[v + dy]:
                if fl[v - dy]: out.append((v, WALK))                                   # level ground
                else:
                    # a drop of one to three on to ground, or a block laid over the void
                    w = v - dy; k = 1
                    while k <= 3 and op[w] and not fl[w - dy]: w -= dy; k += 1
                    if k <= 3 and op[w] and fl[w - dy]: out.append((w, WALK + DROP))
                    if blo <= uy <= bhi: out.append((v, BRIDGE))
            elif op[u + 2 * dy] and op[v + dy] and op[v + 2 * dy] and fl[v]: out.append((v + dy, UP))       # a jump on to a block one higher
        if ug:
            for stp, a, b2 in diag:
                v = u + stp
                if op[v] and op[v + dy] and fl[v - dy] and op[u + a] and op[u + a + dy] and op[u + b2] and op[u + b2 + dy] and fl[u + a - dy] and fl[u + b2 - dy]:
                    out.append((v, DIAG))
        if op[u + 2 * dy] and blo <= uy < bhi + 3: out.append((u + dy, TOWER))        # a block under the feet
        for v, c in out:
            nd = d + c
            if nd < dist.get(v, 1e18): dist[v] = nd; par[v] = u; heapq.heappush(pq, (nd, v))
    res = {}
    for t in targets:
        i = g.idx(*t)
        if i not in par: continue
        path = []
        while i != -1: path.append(g.pos(i)); i = par[i]
        res[t] = (dist[g.idx(*t)], path[::-1])
    return res

def simplify(path):
    """keep the corners, every change of height, and the first and last cell of every stretch over the void"""
    if len(path) <= 2: return list(path)
    out = [path[0]]
    for a, b, c in zip(path, path[1:], path[2:]):
        d1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2]); d2 = (c[0] - b[0], c[1] - b[1], c[2] - b[2])
        if d1 != d2 or d1[1] != 0: out.append(b)
    out.append(path[-1])
    return out

def straighten(g, path):
    """a stair-stepped stretch over the void becomes one corner: people bridge straight, turn once, and bridge straight again"""
    out = []; i = 0; n = len(path)
    void = lambda p: not g.ground(g.idx(*p))
    while i < n:
        if i + 1 < n and void(path[i + 1]) and path[i + 1][1] == path[i][1]:
            j = i + 1
            while j < n and void(path[j]) and path[j][1] == path[i][1]: j += 1
            # path[i] is the last ground cell, path[j] (if any) the first ground cell again, all at one height in between
            a = path[i]; e = path[min(j, n - 1)]
            if j < n and e[1] == a[1]:
                for legs in (((e[0], a[1], a[2]),), ((a[0], a[1], e[2]),)):
                    corner = legs[0]; cells = _line(a, corner) + _line(corner, e)[1:]
                    if all(g.node(g.idx(*c)) for c in cells) and len(cells) <= (j - i) + 1:
                        out.extend(cells[:-1]); i = j; break
                else:
                    out.extend(path[i:j]); i = j
                continue
            out.extend(path[i:j]); i = j; continue
        out.append(path[i]); i += 1
    return out

def _line(a, b):
    """cells from a to b along one axis"""
    out = [a]; x, y, z = a
    while (x, z) != (b[0], b[2]):
        x += (b[0] > x) - (b[0] < x); z += (b[2] > z) - (b[2] < z); out.append((x, y, z))
    return out

def nearest_stand(g, seen, target, lo=1.0, hi=3.2, prefer=None):
    best = None
    for c in seen:
        d = math.dist((c[0], c[2]), (target[0], target[2]))
        if abs(c[1] - target[1]) <= 1 and lo <= d <= hi:
            k = (d + 3 * abs(c[1] - target[1]) + (0.02 * math.dist((c[0], c[2]), (prefer[0], prefer[2])) if prefer else 0), c)
            if best is None or k < best: best = k
    return best[1] if best else None

def flood(g, s, limit=6000):
    """every cell that can be walked to from s without building"""
    import collections
    seen = {s}; dq = collections.deque([s])
    while dq and len(seen) < limit:
        x, y, z = dq.popleft()
        for ddx, ddz in CARD:
            for ddy in (1, 0, -1, -2, -3):
                q = (x + ddx, y + ddy, z + ddz)
                if g.stand(*q):
                    if ddy == 1 and not g.op[g.idx(x, y + 2, z)]: continue
                    if ddy < 0 and not all(g.op[g.idx(x + ddx, y + j, z + ddz)] for j in range(ddy, 2)): continue
                    if q not in seen: seen.add(q); dq.append(q)
                    break
    return seen

MAXDROP = 6
def steps(g, c):
    """the cells a bot gets to from c in one step without building: level, one up (a jump), or down as far as six
    (more than three hurts a little: a person who has lost the way jumps all the same)"""
    x, y, z = c; out = []
    for k, (ddx, ddz) in enumerate(CARD):
        for ddy in (1, 0, -1, -2, -3, -4, -5, -6):
            q = (x + ddx, y + ddy, z + ddz)
            if g.stand(*q):
                if ddy == 1 and not g.op[g.idx(x, y + 2, z)]: continue
                if ddy < 0 and not all(g.op[g.idx(x + ddx, y + j, z + ddz)] for j in range(ddy, 2)): continue
                out.append((q, k, ddy)); break
    return out

def flow(g, b, hubs):
    """For every cell of the map a bot can stand on: the next step of the shortest walk (no building) to the nearest hub.
    A bot that has lost its way looks its cell up here and walks home step by step - the thing a person does by looking around.
    Returns {cell: code}; code = 1 + direction * 8 + (dy + 6), direction as in CARD; a hub's own cell has 40."""
    cells = [(x, y + 1, z) for (x, y, z) in b if g.stand(x, y + 1, z)]
    back = {}
    for c in cells:
        for q, k, ddy in steps(g, c):
            back.setdefault(q, []).append((c, k, ddy))
    dist = {h: 0.0 for h in hubs}; code = {h: 40 for h in hubs}; pq = [(0.0, h) for h in hubs]; heapq.heapify(pq)
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]: continue
        for c, k, ddy in back.get(u, ()):
            nd = d + (WALK if ddy == 0 else UP if ddy == 1 else WALK + DROP + 4.0 * max(0, -ddy - 3))
            if nd < dist.get(c, 1e18): dist[c] = nd; code[c] = 1 + k * 8 + (ddy + 6); heapq.heappush(pq, (nd, c))
    return code, len(cells)

def escapes(g, fl, cells, reach=22, maxup=34):
    """Ground a bot can stand on but cannot walk home from - a ledge under an island, the top of a planet it fell on.
    For each such patch: a way out that a bot can build (a pillar where the sky is open, then a bridge, one turn at most) to the nearest
    ground that does lead home, and for every cell of the patch the next step to the foot of that pillar.
    Returns ({cell: code}, {foot cell: (points to walk, the cell of known ground they end on)}); a foot has code 50."""
    import collections
    miss = set(c for c in cells if c not in fl)
    if not miss: return {}, {}
    back = {}; und = collections.defaultdict(set)
    for c in miss:
        for q, k, ddy in steps(g, c):
            if q in miss: back.setdefault(q, []).append((c, k, ddy)); und[c].add(q); und[q].add(c)
    buckets = {}
    for f in fl: buckets.setdefault((f[0] >> 3, f[2] >> 3), []).append(f)
    op, idx, dy = g.op, g.idx, g.dy
    def clear(x, y, z):
        i = idx(x, y, z); return op[i] and op[i + dy]
    def leg(x0, z0, x1, z1, y):
        x, z = x0, z0
        while (x, z) != (x1, z1):
            x += (x1 > x) - (x1 < x); z += (z1 > z) - (z1 < z)
            if not clear(x, y, z): return False
        return True
    def way(c, f, p=None):
        """c: where the bot stands; p: where its pillar goes up (c itself, or a cell it bridges out to first); f: known ground"""
        p = p or c
        h = max(f[1], p[1])
        if h > p[1] and not all(op[idx(p[0], y, p[2])] for y in range(p[1] + 2, h + 2)): return None
        for cx_, cz_ in ((f[0], p[2]), (p[0], f[2])):
            if not (leg(p[0], p[2], cx_, cz_, h) and leg(cx_, cz_, f[0], f[2], h)): continue
            pts = ([p] if p != c else []) + [(p[0], y, p[2]) for y in range(p[1] + 12, h, 12)] + ([(p[0], h, p[2])] if h > p[1] else [])
            if (cx_, cz_) not in ((p[0], p[2]), (f[0], f[2])): pts.append((cx_, h, cz_))
            pts.append(f)
            return pts
        return None
    def way_out(c, f):
        """... the pillar a few steps to the side, where there is nothing overhead"""
        for k in range(1, 15):
            for ddx, ddz in CARD:
                p = (c[0] + ddx * k, c[1], c[2] + ddz * k)
                if abs(p[0] - f[0]) > reach + 6 or abs(p[2] - f[2]) > reach + 6: continue
                if not leg(c[0], c[2], p[0], p[2], c[1]): continue
                pts = way(c, f, p)
                if pts: return pts, 5 * k
        return None, 0
    codes = {}; exits = {}; seen = set(); stats = [0, 0, 0]
    for start in sorted(miss):
        if start in seen: continue
        comp = [start]; seen.add(start); dq = [start]
        while dq:
            u = dq.pop()
            for v in und[u]:
                if v not in seen: seen.add(v); comp.append(v); dq.append(v)
        stats[0] += 1; left = set(comp)
        for _ in range(80):                                  # a patch may need many ways out (the steps down its sides go one way only)
            if not left: break
            # where to try: cells with nothing overhead first (a pillar can go straight up there), spread over the patch
            top = g.y0 + g.sy - 4
            sky = sorted((c for c in left if all(op[idx(c[0], y, c[2])] for y in range(c[1] + 2, top))), key=lambda c: (-c[1], c))
            rest = sorted(left - set(sky), key=lambda c: (-c[1], c))
            cand = sky[::max(1, len(sky) // 30)][:30] + rest[::max(1, len(rest) // 14)][:14]
            best = None
            for c in cand:
                near = []
                for bx in range((c[0] - reach) >> 3, ((c[0] + reach) >> 3) + 1):
                    for bz in range((c[2] - reach) >> 3, ((c[2] + reach) >> 3) + 1): near += buckets.get((bx, bz), ())
                near = [(8 * max(0, f[1] - c[1]) + 5 * (abs(f[0] - c[0]) + abs(f[2] - c[2])) + 2 * max(0, c[1] - f[1]), f) for f in near
                        if abs(f[0] - c[0]) <= reach and abs(f[2] - c[2]) <= reach and -3 <= f[1] - c[1] <= maxup]
                near.sort()
                found = False
                for est, f in near[:60]:
                    if best and est >= best[0]: break
                    pts = way(c, f)
                    if pts: best = (est, c, f, pts); found = True; break
                if not found:
                    for est, f in near[:10]:
                        if best and est >= best[0]: break
                        pts, extra = way_out(c, f)
                        if pts and (not best or est + extra < best[0]): best = (est + extra, c, f, pts); break
            if not best: break
            est, c, f, pts = best
            exits[c] = (pts, f); codes[c] = 50; stats[1] += 1
            dist = {c: 0}; dq = collections.deque([c])
            while dq:
                u = dq.popleft()
                for p, k, ddy in back.get(u, ()):
                    if p in left and p not in dist: dist[p] = dist[u] + 1; codes[p] = 1 + k * 8 + (ddy + 6); dq.append(p)
            left -= set(dist)
        stats[2] += len(comp) - len(left)
    return codes, exits, (len(miss), *stats)

def plan(mid, out_dir, verbose=True):
    d = pickle.load(open(f'{out_dir}/canvas/{mid}.pkl', 'rb')); b = d['b']
    key = hashlib.md5(pickle.dumps(sorted(b.items())) + open(__file__, 'rb').read()).hexdigest()
    cf = f'{out_dir}/nav_{mid}.json'
    if os.path.exists(cf):
        old = json.load(open(cf))
        if old.get('key') == key: return old
    t0 = time.time()
    T = {}; dia = []; em = []
    for p, tags in d['ents']:
        tags = set(tags); cell = (math.floor(p[0]), math.floor(p[1]), math.floor(p[2]))
        team = next((t[5:] for t in tags if t.startswith('bw.t.')), None)
        if 'bw.gen.diamond' in tags: dia.append(cell)
        elif 'bw.gen.emerald' in tags: em.append(cell)
        elif team and 'bw.gui' not in tags:
            for k in ('spawn', 'bed', 'shop', 'upgrade'):
                if 'bw.' + k in tags: T.setdefault(team, {})[k] = cell
            if 'bw.gen.iron' in tags: T.setdefault(team, {})['gen'] = cell
    dia.sort(); em.sort()
    ys = [t[k][1] for t in T.values() for k in ('spawn', 'gen', 'bed')] + [c[1] for c in dia + em]
    g = Grid(b, ylo=min(ys) - 1, yhi=max(ys) + 1)
    nodes = {}; alt = {}; defs = {}
    for i, team in enumerate(TEAMS):
        t = T[team]; seen = flood(g, t['spawn'])
        assert g.stand(*t['spawn']), (mid, team, 'spawn')
        nodes[f's{i}'] = t['spawn']
        nodes[f'g{i}'] = t['gen'] if t['gen'] in seen else nearest_stand(g, seen, t['gen'], 0, 2.5)
        nodes[f'k{i}'] = nearest_stand(g, seen, t['shop'], 1.0, 3.2, prefer=t['spawn'])
        bs = b[t['bed']]; props = check.props(bs); ddx, ddz = check.DV[props['facing']]
        head = (t['bed'][0] + ddx, t['bed'][1], t['bed'][2] + ddz); mid_b = ((t['bed'][0] + head[0]) / 2, t['bed'][1], (t['bed'][2] + head[2]) / 2)
        # where an attacker stands: next to the bed, on the side of the map's middle first
        cand = sorted((c for c in seen if abs(c[1] - t['bed'][1]) <= 1 and 1.2 <= math.dist((c[0], c[2]), (mid_b[0], mid_b[2])) <= 2.6),
                      key=lambda c: (math.hypot(c[0], c[2]), c))
        assert cand, (mid, team, 'no cell next to the bed')
        nodes[f'a{i}'] = cand[0]
        # where the team's own bot stands to build the defence: outside the shell, an arm's length from the bed
        far = sorted((c for c in seen if abs(c[1] - t['bed'][1]) <= 1 and 3.4 <= math.dist((c[0], c[2]), (mid_b[0], mid_b[2])) <= 4.6),
                     key=lambda c: (abs(c[1] - t['bed'][1]), math.dist(c, t['gen']), c))
        assert far, (mid, team, 'no cell to build from')
        nodes[f'b{i}'] = far[0]
        alt[i] = [cand[0]] + [c for c in cand[1:] if math.dist(c, cand[0]) > 2.0][:3]
        beds = {t['bed'], head}
        l1 = sorted({(x + ex, y + ey, z + ez) for (x, y, z) in beds for ex, ey, ez in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0))} - beds, key=lambda c: (c[1], c))
        l1 = [c for c in l1 if c not in b]
        l2 = sorted({(x + ex, y + ey, z + ez) for (x, y, z) in l1 for ex, ey, ez in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0))} - beds - set(l1), key=lambda c: (c[1], c))
        l2 = [c for c in l2 if c not in b and c[1] >= t['bed'][1]]
        defs[i] = dict(l1=l1, l2=l2, bed=[t['bed'], head])
    for k, c in enumerate(dia): nodes[f'd{k}'] = c
    for k, c in enumerate(em): nodes[f'e{k}'] = c
    for n, c in nodes.items(): assert c and g.stand(*c), (mid, n, c)
    hint = nearest_stand(g, flood(g, dia[0]), dia[0], 2.0, 4.5) if dia else None          # where the stranger with the hints stands
    N = len(TEAMS); nd = len(dia); ne = len(em)
    want = {}
    for i in range(N):
        want[f's{i}'] = [f'g{i}']; want[f'k{i}'] = [f'g{i}']
        want[f'b{i}'] = [f'g{i}']
        want[f'g{i}'] = [f'k{i}', f'b{i}'] + [f'a{j}' for j in range(N)] + [f'd{k}' for k in range(nd)] + [f'e{k}' for k in range(ne)]
        want[f'a{i}'] = [f'g{j}' for j in range(N)] + [f'a{j}' for j in range(N) if j != i]
    for k in range(nd): want[f'd{k}'] = [f'g{j}' for j in range(N)] + [f'a{j}' for j in range(N)]
    for k in range(ne): want[f'e{k}'] = [f'g{j}' for j in range(N)]
    routes = {}; cost = {}
    for src, tg in want.items():
        res = dijkstra(g, nodes[src], [nodes[t] for t in tg], limit=60 if src[0] in 'skb' else None)
        for t in tg:
            if nodes[t] not in res: print('  NAV', mid, 'no way', src, t); continue
            c, path = res[nodes[t]]
            path = simplify(straighten(g, path))
            routes[f'{src}_{t}'] = path[1:] if len(path) > 1 else path; cost[f'{src}_{t}'] = round(c, 1)
    # who lives next to whom: the two cheapest beds to reach from each forge
    near = {i: sorted((j for j in range(N) if j != i), key=lambda j: cost.get(f'g{i}_a{j}', 1e9)) for i in range(N)}
    neard = {i: sorted(range(nd), key=lambda k: cost.get(f'g{i}_d{k}', 1e9)) for i in range(N)}
    neare = {i: sorted(range(ne), key=lambda k: cost.get(f'g{i}_e{k}', 1e9)) for i in range(N)}
    # the way home from anywhere: to the nearest bed-side, diamond or emerald point (from each of those there is a planned way on)
    hubs = {tuple(c): n for n, c in nodes.items() if n[0] in 'ade'}
    fl, nstand = flow(g, b, list(hubs))
    cells_all = [(x, y + 1, z) for (x, y, z) in b if g.stand(x, y + 1, z)]
    esc_codes, esc, esc_stats = escapes(g, fl, cells_all)
    flow_out = [[c[0], c[1], c[2], v] for c, v in sorted({**fl, **esc_codes}.items())]
    esc_out = [[list(c), [list(p) for p in pts], list(f)] for c, (pts, f) in sorted(esc.items())]
    # and the way to the nearest forge: a bot on its own island that wants to go home walks straight there
    forges = {tuple(c): n for n, c in nodes.items() if n[0] == 'g'}
    fg, _ = flow(g, b, list(forges))
    flowg_out = [[c[0], c[1], c[2], v] for c, v in sorted(fg.items())]
    hubs.update(forges)
    hub_out = {f'{c[0]} {c[1]} {c[2]}': n for c, n in hubs.items()}
    out = dict(key=key, nodes=nodes, routes=routes, cost=cost, defs=defs, alt=alt, near=near, neard=neard, neare=neare, nd=nd, ne=ne, hint=hint, dia0=dia[0] if dia else None, flow=flow_out, flowg=flowg_out, hubs=hub_out, nstand=nstand, esc=esc_out)
    out = json.loads(json.dumps(out))
    json.dump(out, open(cf, 'w'))
    if verbose:
        ln = [len(r) for r in routes.values()]
        print(f'nav {mid:8s} nodes {len(nodes)} routes {len(routes)} points {sum(ln)} longest {max(ln)} | flow {len(fl)} + {len(fg)} (home) of {nstand} standable cells; off the ways: {esc_stats[0]} cells in {esc_stats[1]} patches, {esc_stats[2]} ways out reach {esc_stats[3]} cells  {time.time() - t0:.0f}s', flush=True)
    return out

if __name__ == '__main__':
    out = os.environ.get('BW_OUT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/out3'
    for mid in sys.argv[1:] or ['tea', 'chess', 'circus', 'library', 'solar']:
        r = plan(mid, out)
        c = r['cost']; print('  g0->a1', c.get('g0_a1'), 'g0->a4', c.get('g0_a4'), 'g0->d', [c.get(f'g0_d{k}') for k in range(r['nd'])], 'g0->e0', c.get('g0_e0'), 'near0', r['near']['0'][:3])

"""Voxel canvas for Minecraft Java 26.3: block-state helpers (rotate / mirror), noise, structure-file writer."""
import math, random, re, os
import numpy as np
import nbtlib
from nbtlib import Compound, List, Int, String, Double

DATA_VERSION = 5023
DIRS = ('north', 'east', 'south', 'west')
ROT = {'north': 'east', 'east': 'south', 'south': 'west', 'west': 'north'}
MIR = {'east': 'west', 'west': 'east'}

def parse(state):
    m = re.match(r'^([a-z0-9_:]+)(?:\[(.*)\])?$', state)
    name = m.group(1)
    if ':' not in name: name = 'minecraft:' + name
    props = {}
    if m.group(2):
        for kv in m.group(2).split(','):
            k, v = kv.split('='); props[k.strip()] = v.strip()
    return name, props

def fmt(name, props):
    if not props: return name
    return name + '[' + ','.join(f'{k}={v}' for k, v in sorted(props.items())) + ']'

def _rail(shape, f):
    parts = shape.split('_')
    if parts[0] == 'ascending': return 'ascending_' + f(parts[1])
    a, b = f(parts[0]), f(parts[1])
    for cand in ('north_south', 'east_west', 'south_east', 'south_west', 'north_west', 'north_east'):
        if set(cand.split('_')) == {a, b}: return cand
    return shape

_cache = {}
def xform_state(state, k=0, flip=False):
    """mirror across x (east<->west) first if flip, then rotate k quarter turns clockwise seen from above"""
    k %= 4
    if k == 0 and not flip: return state
    key = (state, k, flip)
    if key in _cache: return _cache[key]
    name, p = parse(state)
    if p:
        steps = ([lambda d: MIR.get(d, d)] if flip else []) + [lambda d: ROT.get(d, d)] * k
        for n, f in enumerate(steps):
            mirror = flip and n == 0
            if 'facing' in p: p['facing'] = f(p['facing'])
            if 'rotation' in p:
                r = int(p['rotation']); p['rotation'] = str((16 - r) % 16 if mirror else (r + 4) % 16)
            if not mirror and 'axis' in p and p['axis'] in ('x', 'z'): p['axis'] = 'z' if p['axis'] == 'x' else 'x'
            dv = {d: p.pop(d) for d in DIRS if d in p}
            for d, v in dv.items(): p[f(d)] = v
            if 'shape' in p and name.endswith('rail'): p['shape'] = _rail(p['shape'], f)
            if mirror:
                if 'shape' in p and 'left' in p['shape']: p['shape'] = p['shape'].replace('left', 'right')
                elif 'shape' in p and 'right' in p['shape']: p['shape'] = p['shape'].replace('right', 'left')
                if p.get('hinge') in ('left', 'right'): p['hinge'] = 'right' if p['hinge'] == 'left' else 'left'
                if p.get('type') in ('left', 'right'): p['type'] = 'right' if p['type'] == 'left' else 'left'
    out = fmt(name, p); _cache[key] = out
    return out

def rot_xz(x, z, k):
    for _ in range(k % 4): x, z = -z, x
    return x, z

class Noise:
    def __init__(self, seed):
        r = np.random.RandomState(seed & 0x7fffffff)
        self.g = r.rand(256, 256); self.g3 = r.rand(64, 64, 64)
    def n2(self, x, z, scale=8.0):
        x /= scale; z /= scale
        xi, zi = math.floor(x), math.floor(z); xf, zf = x - xi, z - zi
        u = xf * xf * (3 - 2 * xf); v = zf * zf * (3 - 2 * zf)
        g = self.g; a = g[xi & 255, zi & 255]; b = g[(xi + 1) & 255, zi & 255]
        c = g[xi & 255, (zi + 1) & 255]; d = g[(xi + 1) & 255, (zi + 1) & 255]
        return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v
    def f2(self, x, z, scale=8.0, oct=3):
        s = 0; amp = 1; tot = 0
        for o in range(oct):
            s += amp * self.n2(x + o * 31.7, z - o * 17.3, scale / (2 ** o)); tot += amp; amp *= 0.5
        return s / tot
    def n3(self, x, y, z, scale=6.0):
        x /= scale; y /= scale; z /= scale
        xi, yi, zi = math.floor(x), math.floor(y), math.floor(z)
        xf, yf, zf = x - xi, y - yi, z - zi
        u = xf * xf * (3 - 2 * xf); v = yf * yf * (3 - 2 * yf); w = zf * zf * (3 - 2 * zf)
        g = self.g3; r = 0.0
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    r += (u if dx else 1 - u) * (v if dy else 1 - v) * (w if dz else 1 - w) * g[(xi + dx) & 63, (yi + dy) & 63, (zi + dz) & 63]
        return r

class Canvas:
    def __init__(self, seed=1):
        self.b = {}; self.nbt = {}; self.ents = []
        self.rng = random.Random(seed); self.noise = Noise(seed); self.seed = seed

    def set(self, x, y, z, s, force=True):
        p = (int(x), int(y), int(z))
        if s is None or s == 'air':
            if force: self.b.pop(p, None); self.nbt.pop(p, None)
            return
        if not force and p in self.b: return
        if ':' not in s.split('[')[0]: s = 'minecraft:' + s
        self.b[p] = s

    def get(self, x, y, z): return self.b.get((int(x), int(y), int(z)))
    def name(self, x, y, z):
        s = self.b.get((int(x), int(y), int(z)))
        return s.split('[')[0].replace('minecraft:', '') if s else None
    def empty(self, x, y, z): return (int(x), int(y), int(z)) not in self.b

    def pick(self, w):
        if isinstance(w, str): return w
        if isinstance(w[0], str): return self.rng.choice(w)
        tot = sum(v for _, v in w); r = self.rng.random() * tot
        for s, v in w:
            r -= v
            if r <= 0: return s
        return w[-1][0]

    def top(self, x, z, y_from=120, y_to=-120):
        for y in range(y_from, y_to, -1):
            if (x, y, z) in self.b: return y
        return None

    def paste(self, other, dx=0, dy=0, dz=0, k=0, flip=False, force=True):
        """paste another canvas: mirror across x if flip, rotate k quarter turns about its origin, then move"""
        hit = 0
        for (x, y, z), s in other.b.items():
            if flip: x = -x
            rx, rz = rot_xz(x, z, k); p = (rx + dx, y + dy, rz + dz)
            if p in self.b:
                hit += 1
                if not force: continue
            self.b[p] = xform_state(s, k, flip)
        for (x, y, z), t in other.nbt.items():
            if flip: x = -x
            rx, rz = rot_xz(x, z, k); self.nbt[(rx + dx, y + dy, rz + dz)] = t
        for (x, y, z), t in other.ents:
            if flip: x = 1 - x
            rx, rz = rot_xz(x - 0.5, z - 0.5, k)
            self.ents.append(((rx + 0.5 + dx, y + dy, rz + 0.5 + dz), t))
        return hit

    def marker(self, x, y, z, tags):
        self.ents.append(((x + 0.5, float(y), z + 0.5), Compound({'id': String('minecraft:marker'), 'Tags': List[String]([String(t) for t in tags])})))

    def bounds(self):
        P = np.array(list(self.b.keys())); return P.min(0), P.max(0)

    def footprint(self): return {(x, z) for (x, y, z) in self.b}

    def save_structure(self, path):
        (x0, y0, z0), (x1, y1, z1) = self.bounds()
        palette = {}; plist = []; blocks = []
        for (x, y, z), s in self.b.items():
            i = palette.get(s)
            if i is None:
                i = palette[s] = len(plist)
                name, props = parse(s); e = Compound({'id': String(name)})
                if props: e['properties'] = Compound({k: String(v) for k, v in props.items()})
                plist.append(e)
            c = Compound({'pos': List[Int]([Int(x - x0), Int(y - y0), Int(z - z0)]), 'state': Int(i)})
            if (x, y, z) in self.nbt: c['nbt'] = self.nbt[(x, y, z)]
            blocks.append(c)
        ents = [Compound({'pos': List[Double]([Double(x - x0), Double(y - y0), Double(z - z0)]),
                          'blockPos': List[Int]([Int(math.floor(x) - x0), Int(math.floor(y) - y0), Int(math.floor(z) - z0)]), 'nbt': t})
                for (x, y, z), t in self.ents]
        root = Compound({'DataVersion': Int(DATA_VERSION), 'size': List[Int]([Int(x1 - x0 + 1), Int(y1 - y0 + 1), Int(z1 - z0 + 1)]),
                         'palette': List[Compound](plist), 'blocks': List[Compound](blocks), 'entities': List[Compound](ents)})
        nbtlib.File(root).save(path, gzipped=True)
        return (int(x0), int(y0), int(z0)), (int(x1 - x0 + 1), int(y1 - y0 + 1), int(z1 - z0 + 1)), len(blocks), len(plist)

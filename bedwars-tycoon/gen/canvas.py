"""Voxel canvas, noise, block-state helpers and the structure-file writer for Minecraft Java 26.3."""
import math, random, re, gzip, io
import numpy as np
import nbtlib
from nbtlib import Compound, List, Int, String, Double, IntArray

DATA_VERSION = 5023

# ------------------------------------------------------------------ block states
def parse(state):
    """'minecraft:oak_stairs[facing=east,half=top]' -> ('minecraft:oak_stairs', {'facing': 'east', 'half': 'top'})"""
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

ROT_FACING = {'north': 'east', 'east': 'south', 'south': 'west', 'west': 'north'}

def rotate_state(state, k):
    """rotate a block state k quarter turns clockwise (seen from above)"""
    k %= 4
    if k == 0: return state
    name, p = parse(state)
    for _ in range(k):
        if 'facing' in p and p['facing'] in ROT_FACING: p['facing'] = ROT_FACING[p['facing']]
        if 'axis' in p and p['axis'] in ('x', 'z'): p['axis'] = 'z' if p['axis'] == 'x' else 'x'
        if 'rotation' in p: p['rotation'] = str((int(p['rotation']) + 4) % 16)
        if all(d in p for d in ('north', 'east', 'south', 'west')):
            p['north'], p['east'], p['south'], p['west'] = p['west'], p['north'], p['east'], p['south']
        if 'shape' in p and ('stairs' in name):
            pass   # stair shapes are recomputed by the game when neighbours update; straight is fine
    return fmt(name, p)

def rot_xz(x, z, k):
    for _ in range(k % 4):
        x, z = -z, x
    return x, z

# ------------------------------------------------------------------ noise
class Noise:
    """smooth value noise in 2D/3D, deterministic per seed"""
    def __init__(self, seed):
        self.r = np.random.RandomState(seed & 0x7fffffff)
        self.g = self.r.rand(256, 256)
        self.g3 = self.r.rand(64, 64, 64)
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
                    wt = (u if dx else 1 - u) * (v if dy else 1 - v) * (w if dz else 1 - w)
                    r += wt * g[(xi + dx) & 63, (yi + dy) & 63, (zi + dz) & 63]
        return r

# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, seed=1):
        self.b = {}                 # (x,y,z) -> state string
        self.nbt = {}               # (x,y,z) -> block entity nbt (Compound) for chests, banners...
        self.ents = []              # (x,y,z float, Compound)
        self.rng = random.Random(seed)
        self.noise = Noise(seed)
        self.protect = set()        # positions decor must not overwrite

    def set(self, x, y, z, s, force=True):
        p = (int(x), int(y), int(z))
        if not force and p in self.b: return
        if p in self.protect and not force: return
        if s is None or s == 'air' or s == 'minecraft:air':
            self.b.pop(p, None); return
        if ':' not in s.split('[')[0]: s = 'minecraft:' + s
        self.b[p] = s

    def get(self, x, y, z):
        return self.b.get((int(x), int(y), int(z)))

    def empty(self, x, y, z):
        return (int(x), int(y), int(z)) not in self.b

    def box(self, x0, y0, z0, x1, y1, z1, s, hollow=False, force=True):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    if hollow and min(x0, x1) < x < max(x0, x1) and min(y0, y1) < y < max(y0, y1) and min(z0, z1) < z < max(z0, z1):
                        continue
                    self.set(x, y, z, s, force)

    def pick(self, weighted):
        """weighted: list of (state, weight) or plain list"""
        if isinstance(weighted, str): return weighted
        if isinstance(weighted[0], str): return self.rng.choice(weighted)
        tot = sum(w for _, w in weighted); r = self.rng.random() * tot
        for s, w in weighted:
            r -= w
            if r <= 0: return s
        return weighted[-1][0]

    def top(self, x, z, y_from=400, y_to=-100):
        for y in range(y_from, y_to, -1):
            if (x, y, z) in self.b: return y
        return None

    def paste(self, other, dx, dy, dz, k=0, force=True):
        """paste another canvas, rotated k quarter turns about its origin, then moved; returns how many blocks it overlapped"""
        hit = 0
        for (x, y, z), s in other.b.items():
            rx, rz = rot_xz(x, z, k)
            if (rx + dx, y + dy, rz + dz) in self.b: hit += 1
            self.set(rx + dx, y + dy, rz + dz, rotate_state(s, k), force)
        for (x, y, z), t in other.nbt.items():
            rx, rz = rot_xz(x, z, k); self.nbt[(rx + dx, y + dy, rz + dz)] = t
        for (x, y, z), t in other.ents:
            rx, rz = rot_xz(x - 0.5, z - 0.5, k); rx += 0.5; rz += 0.5      # rotate about the block centre
            t = Compound(t)
            if 'Rotation' in t:
                t['Rotation'] = List[nbtlib.Float]([nbtlib.Float(float(t['Rotation'][0]) + 90 * k), t['Rotation'][1]])
            self.ents.append(((rx + dx, y + dy, rz + dz), t))
        return hit

    def marker(self, x, y, z, tags, data=None):
        c = Compound({'id': String('minecraft:marker'), 'Tags': List[String]([String(t) for t in tags])})
        if data: c['data'] = data
        self.ents.append(((x + 0.5, y, z + 0.5), c))

    def bounds(self):
        P = np.array(list(self.b.keys()))
        return P.min(0), P.max(0)

    # -------------------------------------------------------------- structure file
    def save_structure(self, path, key_style='id'):
        (x0, y0, z0), (x1, y1, z1) = self.bounds()
        palette = {}; plist = []; blocks = []
        for (x, y, z), s in self.b.items():
            if s not in palette:
                palette[s] = len(plist)
                name, props = parse(s)
                if key_style == 'id':
                    e = Compound({'id': String(name)})
                    if props: e['properties'] = Compound({k: String(v) for k, v in props.items()})
                else:
                    e = Compound({'Name': String(name)})
                    if props: e['Properties'] = Compound({k: String(v) for k, v in props.items()})
                plist.append(e)
            c = Compound({'pos': List[Int]([Int(x - x0), Int(y - y0), Int(z - z0)]), 'state': Int(palette[s])})
            if (x, y, z) in self.nbt: c['nbt'] = self.nbt[(x, y, z)]
            blocks.append(c)
        ents = []
        for (x, y, z), t in self.ents:
            ents.append(Compound({'pos': List[Double]([Double(x - x0), Double(y - y0), Double(z - z0)]),
                                  'blockPos': List[Int]([Int(math.floor(x) - x0), Int(math.floor(y) - y0), Int(math.floor(z) - z0)]),
                                  'nbt': t}))
        root = Compound({'DataVersion': Int(DATA_VERSION),
                         'size': List[Int]([Int(x1 - x0 + 1), Int(y1 - y0 + 1), Int(z1 - z0 + 1)]),
                         'palette': List[Compound](plist), 'blocks': List[Compound](blocks), 'entities': List[Compound](ents)})
        f = nbtlib.File(root); f.save(path, gzipped=True)
        return (x0, y0, z0), (x1 - x0 + 1, y1 - y0 + 1, z1 - z0 + 1), len(blocks), len(plist)

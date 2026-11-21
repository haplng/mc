"""Read block states from a 26.3 world's region files (to compare what the game actually kept with what was intended)."""
import os, struct, zlib, io, math
import numpy as np
import nbtlib

def _state(e):
    if isinstance(e, str): return str(e)
    if '' in e: return str(e[''])
    name = str(e.get('Name', e.get('id', '?')))
    props = e.get('Properties', e.get('properties'))
    if props: return name + '[' + ','.join(f'{k}={v}' for k, v in sorted((str(k), str(v)) for k, v in props.items())) + ']'
    return name

def read_region(path):
    data = open(path, 'rb').read()
    if len(data) < 8192: return
    for i in range(1024):
        off = int.from_bytes(data[i * 4:i * 4 + 3], 'big')
        if off == 0: continue
        q = off * 4096; ln = struct.unpack('>I', data[q:q + 4])[0]; comp = data[q + 4]
        raw = data[q + 5:q + 4 + ln]
        if comp == 2: raw = zlib.decompress(raw)
        elif comp == 1:
            import gzip; raw = gzip.decompress(raw)
        elif comp == 3: pass
        else: continue
        yield nbtlib.File.parse(io.BytesIO(raw))

def blocks(world, x0, x1, z0, z1, dim='overworld'):
    """dict (x,y,z) -> state string for all non-air blocks in the given column range"""
    rd = os.path.join(world, 'dimensions', 'minecraft', dim, 'region')
    out = {}
    for rx in range(x0 >> 9, (x1 >> 9) + 1):
        for rz in range(z0 >> 9, (z1 >> 9) + 1):
            p = os.path.join(rd, f'r.{rx}.{rz}.mca')
            if not os.path.exists(p): continue
            for c in read_region(p):
                cx, cz = int(c['xPos']), int(c['zPos'])
                if cx * 16 > x1 or cx * 16 + 15 < x0 or cz * 16 > z1 or cz * 16 + 15 < z0: continue
                for s in c['sections']:
                    bs = s.get('block_states')
                    if bs is None: continue
                    pal = [_state(e) for e in bs['palette']]
                    if len(pal) == 1 and pal[0] in ('minecraft:air',): continue
                    sy = int(s['Y']) * 16
                    if 'data' not in bs:
                        idx = np.zeros(4096, np.int64)
                    else:
                        longs = np.array(bs['data'], dtype=np.int64).astype(np.uint64)
                        bits = max(4, (len(pal) - 1).bit_length())
                        per = 64 // bits; mask = (1 << bits) - 1
                        idx = np.empty(len(longs) * per, np.int64)
                        for k in range(per): idx[k::per] = ((longs >> np.uint64(k * bits)) & np.uint64(mask)).astype(np.int64)
                        idx = idx[:4096]
                    nz = [k for k, name in enumerate(pal) if name not in ('minecraft:air', 'minecraft:cave_air', 'minecraft:void_air')]
                    if not nz: continue
                    sel = np.nonzero(np.isin(idx, nz))[0]
                    for j in sel:
                        y = (j >> 8) + sy; z = ((j >> 4) & 15) + cz * 16; x = (j & 15) + cx * 16
                        if x0 <= x <= x1 and z0 <= z <= z1: out[(int(x), int(y), int(z))] = pal[idx[j]]
    return out

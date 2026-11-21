"""Read 1.8-era Anvil worlds (numeric block ids) into numpy arrays. Read-only; input files are data."""
import os, struct, zlib, gzip, io, sys
import numpy as np
import nbtlib

def level_ids(world):
    lv = nbtlib.load(os.path.join(world, 'level.dat'))
    ids = {}
    try:
        for e in lv['FML']['Registries']['minecraft:blocks']['ids']:
            ids[int(e['V'])] = str(e['K'])
    except Exception:
        pass
    return ids

def chunks(world):
    rd = os.path.join(world, 'region')
    for fn in sorted(os.listdir(rd)):
        if not fn.endswith('.mca'): continue
        data = open(os.path.join(rd, fn), 'rb').read()
        if len(data) < 8192: continue
        for i in range(1024):
            off = int.from_bytes(data[i*4:i*4+3], 'big'); cnt = data[i*4+3]
            if off == 0 or cnt == 0: continue
            p = off * 4096
            ln = struct.unpack('>I', data[p:p+4])[0]; comp = data[p+4]
            raw = data[p+5:p+4+ln]
            raw = zlib.decompress(raw) if comp == 2 else gzip.decompress(raw)
            yield nbtlib.File.parse(io.BytesIO(raw))

def load(world):
    """returns dict (x,y,z)->(id,data) for non-air blocks, plus tile entities and entities"""
    blocks = {}; tiles = []; ents = []
    for c in chunks(world):
        lvl = c['Level']; cx = int(lvl['xPos']); cz = int(lvl['zPos'])
        for s in lvl.get('Sections', []):
            if 'Blocks' not in s: continue
            sy = int(s['Y'])
            b = np.frombuffer(bytes(np.array(s['Blocks'], dtype=np.int8).astype(np.uint8)), dtype=np.uint8).astype(np.int32)
            if 'Add' in s:
                a = np.frombuffer(bytes(np.array(s['Add'], dtype=np.int8).astype(np.uint8)), dtype=np.uint8)
                add = np.empty(4096, dtype=np.int32); add[0::2] = a & 15; add[1::2] = a >> 4
                b = b + (add << 8)
            dd = np.frombuffer(bytes(np.array(s['Data'], dtype=np.int8).astype(np.uint8)), dtype=np.uint8)
            dat = np.empty(4096, dtype=np.int32); dat[0::2] = dd & 15; dat[1::2] = dd >> 4
            nz = np.nonzero(b)[0]
            for idx in nz:
                y = idx >> 8; z = (idx >> 4) & 15; x = idx & 15
                blocks[(cx*16 + x, sy*16 + y, cz*16 + z)] = (int(b[idx]), int(dat[idx]))
        for t in lvl.get('TileEntities', []): tiles.append(t)
        for e in lvl.get('Entities', []): ents.append(e)
    return blocks, tiles, ents

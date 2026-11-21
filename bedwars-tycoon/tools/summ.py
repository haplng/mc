import sys, os, collections, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import oldanvil
import numpy as np
from scipy import ndimage
out = {}
for w in sorted(os.listdir('.')):
    if not os.path.isdir(w) or not os.path.exists(os.path.join(w, 'level.dat')): continue
    try:
        ids = oldanvil.level_ids(w); b, tiles, ents = oldanvil.load(w)
    except Exception as e:
        print(w, 'ERR', e); continue
    if not b: print(w, 'empty'); continue
    P = np.array(list(b.keys()))
    names = [ids.get(v[0], str(v[0])) for v in b.values()]
    keep = np.array([n not in ('minecraft:barrier',) for n in names])
    P = P[keep]
    x0, y0, z0 = P.min(0); x1, y1, z1 = P.max(0)
    g = np.zeros((x1 - x0 + 1, z1 - z0 + 1), bool); g[P[:, 0] - x0, P[:, 2] - z0] = True
    lab, n = ndimage.label(ndimage.binary_dilation(g, iterations=1))
    sizes = np.bincount(lab.ravel())[1:]
    big = sorted([int(s) for s in sizes if s >= 40], reverse=True)
    beds = sorted({(p[0]//1, p[1], p[2]) for p, v in b.items() if ids.get(v[0]) == 'minecraft:bed'})
    cnt = collections.Counter(n for n, k in zip(names, keep) if k)
    out[w] = dict(n=int(len(P)), sx=int(x1-x0+1), sy=int(y1-y0+1), sz=int(z1-z0+1), y0=int(y0), y1=int(y1), islands=len(big), isl=big[:14], beds=len(beds)//2,
                  top=[k.replace('minecraft:', '') + ':' + str(v) for k, v in cnt.most_common(12)])
    o = out[w]; print(f"{w:16s} blocks {o['n']:7d} size {o['sx']}x{o['sz']} h{o['sy']} y{o['y0']}-{o['y1']} islands {o['islands']:3d} beds {o['beds']:2d}  {o['isl'][:9]}", flush=True)
json.dump(out, open('summary.json', 'w'), indent=1)

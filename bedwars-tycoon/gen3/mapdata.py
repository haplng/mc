"""What the game needs to know about each map, read from the built canvases: where every team spawns, sleeps, shops and smelts,
where the diamonds and emeralds appear, and how low the void is. Positions are world coordinates."""
import math, pickle, os
from util import TEAMS

DV = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}

def load(mid, center, out_dir):
    d = pickle.load(open(f'{out_dir}/canvas/{mid}.pkl', 'rb'))
    b = d['b']; ents = d['ents']; cx, cy, cz = center
    W = lambda p: (p[0] + cx, p[1] + cy, p[2] + cz)
    teams = {}; dia = []; em = []; gui = []
    for p, tags in ents:
        tags = set(tags)
        team = next((g[5:] for g in tags if g.startswith('bw.t.')), None)
        cell = (math.floor(p[0]), math.floor(p[1]), math.floor(p[2]))
        if 'bw.gen.diamond' in tags: dia.append(W(cell))
        elif 'bw.gen.emerald' in tags: em.append(W(cell))
        elif 'bw.gui' in tags: gui.append(dict(team=team, kind='shop' if 'bw.gui.shop' in tags else 'team', pos=W(cell)))
        elif team:
            T = teams.setdefault(team, {})
            for k in ('spawn', 'bed', 'shop', 'upgrade'):
                if 'bw.' + k in tags: T[k] = W(cell)
            if 'bw.gen.iron' in tags: T['gen'] = W(cell)
            if 'bw.bed' in tags:
                s = b[cell]; name = s.split('[')[0]; props = dict(kv.split('=') for kv in s[s.index('[') + 1:-1].split(','))
                assert props['part'] == 'foot', s
                dx, dz = DV[props['facing']]
                T['bed_facing'] = props['facing']; T['bed_head'] = W((cell[0] + dx, cell[1], cell[2] + dz)); T['bed_block'] = name.replace('minecraft:', '')
    assert set(teams) == set(TEAMS), teams.keys()
    ys = [y for (x, y, z) in b]
    for T in teams.values():
        sx, sy, sz = T['spawn']; bx, by, bz = T['bed']
        T['yaw'] = round(math.degrees(math.atan2(-(cx - sx), (cz - sz))), 1)          # spawn looking at the middle of the map
    return dict(id=mid, center=center, teams=[teams[t] for t in TEAMS], diamond=sorted(dia), emerald=sorted(em), gui=gui,
                void_y=cy + min(ys) - 6, top_y=cy + max(ys))

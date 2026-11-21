"""Check that blocks which need something under them (plants, torches, dripstone, sand, gravel, crops) always have it,
and that nether portals sit in a complete obsidian frame, during full simulated runs."""
import sys
import os as _os; ROOT = _os.environ.get('EK_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/tools')
import cardtest as C
from sim import Ctx
from collections import Counter

DIRT = {'grass_block', 'dirt', 'farmland', 'coarse_dirt', 'podzol', 'moss_block'}
NETH = {'crimson_nylium', 'warped_nylium', 'soul_soil'} | DIRT
NONSOLID = {'air', 'water', 'lava', 'short_grass', 'poppy', 'dandelion', 'torch', 'wheat', 'crimson_fungus', 'crimson_roots', 'cobweb',
            'nether_portal', 'end_portal', 'fire', 'red_bed', 'pointed_dripstone', 'iron_bars', 'nether_brick_fence', 'lightning_rod', 'chest', 'spawner',
            'end_portal_frame', 'farmland', 'oak_leaves'}
def base(b): return b.split('[')[0]

def check(sm, bad, tag):
    B = sm.blocks
    for (x, y, z), b in list(B.items()):
        n = base(b); below = base(B.get((x, y - 1, z), 'air'))
        if n in ('short_grass', 'poppy', 'dandelion') and below not in DIRT: bad[(tag, n, 'on ' + below)] += 1
        elif n == 'wheat' and below != 'farmland': bad[(tag, n, 'on ' + below)] += 1
        elif n in ('crimson_fungus', 'crimson_roots') and below not in NETH: bad[(tag, n, 'on ' + below)] += 1
        elif n == 'torch' and below in NONSOLID: bad[(tag, n, 'on ' + below, (x, y, z))] += 1
        elif n == 'pointed_dripstone' and below in NONSOLID - {'pointed_dripstone'}: bad[(tag, n, 'on ' + below)] += 1
        elif n in ('sand', 'gravel') and below in ('air', 'water', 'lava', 'short_grass', 'poppy', 'dandelion', 'torch', 'fire'):
            bad[(tag, n, 'over ' + below, (x, y, z))] += 1
        elif n == 'farmland' and base(B.get((x, y + 1, z), 'air')) not in NONSOLID: bad[(tag, n, 'under solid')] += 1
        elif n == 'nether_portal':
            axis = 'x' if 'axis=x' in b or '[' not in b else 'z'
            dx, dz = (1, 0) if axis == 'x' else (0, 1)
            # walk to the edges of the portal interior in its plane
            def run(ddx, ddy, ddz):
                cx, cy, cz = x, y, z
                while base(B.get((cx + ddx, cy + ddy, cz + ddz), 'air')) == 'nether_portal': cx, cy, cz = cx + ddx, cy + ddy, cz + ddz
                return base(B.get((cx + ddx, cy + ddy, cz + ddz), 'air'))
            edges = [run(dx, 0, dz), run(-dx, 0, -dz), run(0, 1, 0), run(0, -1, 0)]
            if any(e != 'obsidian' for e in edges): bad[(tag, n, 'frame edges ' + str(edges), (x, y, z))] += 1

if __name__ == '__main__':
    bad = Counter(); checked = 0
    for stage in range(1, 8):
        sm, pl = C.setup(stage)
        check(sm, bad, f's{stage} build'); checked += 1
        t = 0
        while sm.get('state') == 1 and sm.get('stage') == stage and t < 9000:
            sm.step(); t += 1
            if t % 5 == 0: check(sm, bad, f's{stage} quiet run'); checked += 1
    # card events too: every card variant, checking every few ticks
    for stage, ids in C.pools().items():
        for slot, cid in ids:
            for variant in ('sweet', 'plain', 'block'):
                sm, pl = C.setup(stage)
                if variant == 'block': sm.scores[('#l_' + cid, 'ek')] = 1
                fired = None; t = 0
                while sm.get('state') == 1 and sm.get('stage') == stage and t < 9000:
                    ok = sm.get('intr') == 0 and sm.get('steve') == 1 and (sm.scores.get((pl.id, 'ek.cd'), 0) or 0) <= 0
                    if ok and fired is None and t > 30 and (C.hint(sm, pl, stage, slot) == (variant != 'plain')):
                        sm.scores[('#energy', 'ek')] = 100; pl.data['slot'] = slot; sm.scores[(pl.id, 'ek.use')] = 1; fired = t
                    sm.step(); t += 1
                    if fired is not None and t % 3 == 0: check(sm, bad, f's{stage} {cid}/{variant}'); checked += 1
                    if fired is not None and t - fired > 400: break
    print('snapshots checked:', checked)
    print('PROBLEMS:', len(bad))
    for k, v in sorted(bad.items(), key=lambda kv: -kv[1])[:40]: print('  ', v, k)

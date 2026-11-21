"""Compare what the server kept with what the generator intended (v4: lobby + five maps), and check that the five discarded slots are empty.
usage: python3 verify4.py <world folder>"""
import sys, os, json, pickle, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import newanvil
ROOT = os.environ.get('BW_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
world = sys.argv[1]
info = json.load(open(ROOT + '/out3/maps.json', encoding='utf-8'))
nm = lambda s: s.split('[')[0].replace('minecraft:', '')
tot = collections.Counter()
for it in info:
    x0, y0, z0, x1, y1, z1 = it['box']
    got = newanvil.blocks(world, x0 - 20, x1 + 20, z0 - 20, z1 + 20)
    if it.get('empty'):
        c = collections.Counter(nm(g) for g in got.values())
        print(f"{it['id']:13s} must be empty: {len(got)} blocks left", dict(c.most_common(5)) if c else '')
        tot['left in emptied slots'] += len(got); continue
    cv = pickle.load(open(f"{ROOT}/out3/canvas/{it['id']}.pkl", 'rb'))
    cx, cy, cz = it['center']
    want = {(x + cx, y + cy, z + cz): s for (x, y, z), s in cv['b'].items()}
    miss = collections.Counter(); extra = collections.Counter(); diff = collections.Counter()
    for p, s in want.items():
        g = got.get(p)
        if g is None: miss[nm(s)] += 1
        elif nm(g) != nm(s): diff[(nm(s), nm(g))] += 1
    for p, g in got.items():
        if p not in want: extra[nm(g)] += 1
    print(f"{it['id']:13s} want {len(want):6d} got {len(got):6d} missing {sum(miss.values()):4d} extra {sum(extra.values()):4d} changed {sum(diff.values())}")
    for label, c in (('missing', miss), ('extra', extra), ('changed', diff)):
        if c: print('    ', label, dict(c.most_common(8)))
    tot['missing'] += sum(miss.values()); tot['extra'] += sum(extra.values()); tot['changed'] += sum(diff.values())
print('TOTAL', dict(tot) or 'all exact, emptied slots empty')

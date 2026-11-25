# -*- coding: utf-8 -*-
"""경제 시뮬레이터(sim.c)가 쓸 표를 만든다:  python3 simgen.py OUTDIR
   (src/tiers.json, hands.py, adv.py, jokers.py, common.py 를 읽는다)
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import hands as HM
import common as CM
import adv as ADV
from jokers import JOKERS
import refgen

out = sys.argv[1]
tiers = json.load(open(os.path.join(HERE, '..', 'src', 'tiers.json'), encoding='utf-8'))['hands']
open(os.path.join(out, 'ref_hands.h'), 'w').write(refgen.build({h['key']: tiers.get(h['key'], {}).get('tier', 0) for h in HM.HANDS}))
idx = {h['key']: i for i, h in enumerate(HM.HANDS)}
FAMJ = {'same': 1, 'stair': 2, 'mirror': 3, 'word': 4, 'combo': 4}
L = []
real = [not (h['eng'] and h['eng'][0] == 'alias') for h in HM.HANDS]
L.append('static const int REAL[NHAND] = {%s};' % ', '.join('1' if r else '0' for r in real))
L.append('static const long PAYB[NHAND] = {%s};' % ', '.join(str(tiers[h['key']]['pay']) if r else '0' for h, r in zip(HM.HANDS, real)))
L.append('static const int FAMJ[NHAND] = {%s};' % ', '.join(str(FAMJ.get(h['fam'], 0)) for h in HM.HANDS))
L.append('static const int STAR_T[6][4] = {%s};' % ', '.join('{%s}' % ', '.join(map(str, r)) for r in CM.STAR_T))
L.append('static const int SPEED_T[11] = {%s};' % ', '.join(map(str, CM.SPEED_T)))
L.append('static const int AUTO_END[11] = {%s};' % ', '.join(map(str, CM.AUTO_END)))
for nm in ('COST_U1', 'COST_U2', 'COST_U3', 'COST_U4'):
    v = getattr(CM, nm)
    L.append('static const long %s[%d] = {%s}; static const int N_%s = %d;' % (nm, len(v), ', '.join(map(str, v)), nm, len(v)))
L.append('static const double UNLP[%d] = {%s}; static const char *UNLN[%d] = {%s};' % (
    len(CM.UNLOCKS), ', '.join('%d.0' % u[2] for u in CM.UNLOCKS), len(CM.UNLOCKS), ', '.join('"%s"' % u[0] for u in CM.UNLOCKS)))
L.append('#define NUNL %d' % len(CM.UNLOCKS))
for k in ('ms1', 'ms2', 'ms3', 't4', 't5', 'jk1', 'jk2', 'jk3', 'jk4', 'dice'):
    L.append('#define ST_%s %d' % (k, CM.unl_stage(k)))
L.append('static const long MISB[3] = {%s}; static const int MISL[3] = {%s}; static const int MISST[3] = {%s};' % (
    ', '.join(str(m[4]) for m in CM.MISSIONS), ', '.join(str(m[3]) for m in CM.MISSIONS), ', '.join(str(CM.unl_stage(m[5])) for m in CM.MISSIONS)))
L.append('static const double MISK[3] = {%s};' % ', '.join(str(m[6]) for m in CM.MISSIONS))
L.append('#define NJOK %d' % len(JOKERS))
L.append('static const double JOKP[NJOK] = {%s};' % ', '.join('%d.0' % j['price'] for j in JOKERS))
L.append('static const char *JOKN[NJOK] = {%s};' % ', '.join('"%s"' % j['name'] for j in JOKERS))
KINDS = ['part', 'digit', 'nh_le', 'nh_ge', 'tiers', 'manual', 'auto', 'found', 'stars', 'cdig', 'mission']
PARTS = ['p0', 'p12', 'p3', 'same', 'stair', 'mirror', 'word']
L.append('enum {%s};' % ', '.join('K_' + k for k in KINDS))
L.append('enum {%s};' % ', '.join('PT_' + k for k in PARTS))
rows = []
for j in JOKERS:
    k = j['kind']
    a = list(k[1:]) + [0, 0]
    if k[0] == 'part':
        a[0] = 'PT_' + k[1]
    rows.append('{K_%s, %s, %s}' % (k[0], a[0], a[1]))
L.append('static const struct { int kind, a, b; } JOK[NJOK] = {%s};' % ', '.join(rows))
for i, (sc, icon, nm, costs, tip, eff) in enumerate(CM.PERKS):
    L.append('static const int PERKC_%s[%d] = {%s}; static const int N_PERK_%s = %d;' % (sc, len(costs), ', '.join(map(str, costs)), sc, len(costs)))
# 도전과제
STATS = ['rolls', 'u2', 'arl', 'found', 'mxt', 'coins', 'cq', 'cb', 'ubuy', 'mxn', 'mxr', 'zn', 'smax', 's5n', 'stot', 'mdone', 'u1', 'u3', 'u4', 'unl', 'pbuy', 'e5', 'jown', 'jeq', 'muted']
L.append('enum {%s, NSTAT};' % ', '.join('S_' + s for s in STATS))
rows = []
cols = []
for a in ADV.A:
    k = a['kind']
    reward = a['reward']
    if k == 'hand':
        rows.append('{"%s", 2, %d, 0, %d.0}' % (a['key'], idx[a['arg']], reward))
    elif k == 'stat':
        rows.append('{"%s", 1, S_%s, %d, %d.0}' % (a['key'], a['arg'][0], a['arg'][1], reward))
    elif k == 'tier':
        n = sum(1 for h, r in zip(HM.HANDS, real) if r and tiers[h['key']]['tier'] == a['arg'])
        rows.append('{"%s", 3, %d, %d, %d.0}' % (a['key'], a['arg'], n, reward))
    elif k == 'col':
        hs = [idx[h['key']] for h, r in zip(HM.HANDS, real) if r and h['tag'] == a['arg']]
        cols.append('static const int COL_%s[] = {%s, -1};' % (a['arg'], ', '.join(map(str, hs))))
        rows.append('{"%s", 4, %d, 0, %d.0}' % (a['key'], len(cols) - 1, reward))
    elif k == 'cond':
        rows.append('{"%s", 5, 0, 0, %d.0}' % (a['key'], reward))
    else:
        rows.append('{"%s", 0, 0, 0, %d.0}' % (a['key'], reward))
L.extend(cols)
names = [c.split('[')[0].split()[-1] for c in cols]
L.append('static const int *COLS[] = {%s};' % ', '.join(names))
L.append('typedef struct { const char *key; int kind, a; double b; double reward; } Adv;')
L.append('static const Adv ADVS[] = {%s};' % ',\n  '.join(rows))
L.append('#define NADV %d' % len(rows))
L.append('static const char *HNAME[NHAND] = {%s};' % ', '.join('"%s"' % h['name'].replace('"', '\\"') for h in HM.HANDS))
open(os.path.join(out, 'sim_data.h'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('ok', len(rows), 'advs')

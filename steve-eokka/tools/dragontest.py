"""Stage 7 geometry check for the visible ender dragon.

The visible dragon is a real (not NoAI) ender dragon. Its wing boxes push living entities that are inside
  wing box inflated by (4, 2, 4) and moved down 2  ->  y from dragonY-2 to dragonY+4, up to ~10.5 blocks sideways.
Steve must never be inside that volume, so this test plays stage 7 with every card fired in every beat and
measures the vertical clearance between the dragon's lowest wing reach and the top of Steve's head.
"""
import sys, math
import os as _os; ROOT = _os.environ.get('EK_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/tools')
import cardtest as C
from sim import Ctx

REACH = 13.0      # horizontal distance inside which the wing volume could matter (10.5 + margin)
NEED = 1.0        # required vertical clearance in blocks

def ent(sm, tag):
    es = [e for e in sm.ents if tag in e.tags]
    return es[0] if es else None

def watch(sm, stats, label):
    d = ent(sm, 'ek.dragon'); v = ent(sm, 'ek.dvis'); s = ent(sm, 'ek.steve')
    if d is None: return
    stats['ticks'] += 1
    x, y, z = d.pos
    stats['ymin'] = min(stats['ymin'], y); stats['ymax'] = max(stats['ymax'], y)
    stats['far'] = max(stats['far'], abs(x), abs(z))
    if v is not None:
        lag = math.dist(d.pos, v.pos); stats['lag'] = max(stats['lag'], lag)
    for other, top in ((s, 1.8),) + tuple((e, 2.9) for e in sm.ents if 'ek.end' in e.tags):
        if other is None: continue
        hd = math.hypot(other.pos[0] - x, other.pos[2] - z)
        if hd > REACH: continue
        clear = (y - 2) - (other.pos[1] + top)
        who = 'steve' if other is s else 'enderman'
        if clear < stats['clear'][who][0]:
            stats['clear'][who] = (clear, label, sm.t, tuple(round(c, 1) for c in d.pos), tuple(round(c, 1) for c in other.pos), sm.get('dmode'))

def run(slot, cid, variant, beat, late, stats):
    sm, pl = C.setup(7)
    if variant == 'block': sm.scores[('#l_' + cid, 'ek')] = 1
    label = f'{cid}/{variant}@beat{beat}{"+late" if late else ""}'
    fired = False; seen = 0
    while sm.get('state') == 1 and sm.get('stage') == 7 and sm.t < 12000:
        watch(sm, stats, label)
        ok = sm.get('intr') == 0 and sm.get('steve') == 1 and (sm.scores.get((pl.id, 'ek.cd'), 0) or 0) <= 0
        if ok and not fired and sm.get('beat') == beat:
            seen += 1
            if seen >= (40 if late else 1):
                sm.scores[('#energy', 'ek')] = 100
                before = C.calls[f'ev/{cid}_hit/start'] + C.calls[f'ev/{cid}_crit/start'] + C.calls[f'ev/{cid}_block/start']
                pl.data['slot'] = slot; sm.scores[(pl.id, 'ek.use')] = 1; sm.step()
                after = C.calls[f'ev/{cid}_hit/start'] + C.calls[f'ev/{cid}_crit/start'] + C.calls[f'ev/{cid}_block/start']
                fired = True
                if after > before: stats['fired'] += 1
                t_end = sm.t + 500
                while sm.t < t_end and sm.get('state') == 1 and sm.get('stage') == 7:
                    watch(sm, stats, label); sm.step()
                break
        if sm.get('beat') is not None and sm.get('beat') > beat and not fired: break
        sm.step()
    if sm.unknown or sm.missing: stats['bad'].append((label, dict(sm.unknown), dict(sm.missing)))

if __name__ == '__main__':
    stats = {'ticks': 0, 'ymin': 999, 'ymax': -999, 'far': 0, 'lag': 0, 'fired': 0, 'bad': [],
             'clear': {'steve': (999,), 'enderman': (999,)}}
    # a full quiet run first
    sm, pl = C.setup(7)
    while sm.get('state') == 1 and sm.get('stage') == 7 and sm.t < 12000:
        watch(sm, stats, 'no cards'); sm.step()
    print('quiet run: ended in state', sm.get('state'), 'res', sm.get('res'), 'after', sm.t, 'ticks; dmode', sm.get('dmode'))
    blen = None
    for line in open(C.OUT + '/data/ek/function/s7/init.mcfunction'):
        if '#blen' in line: blen = int(line.split()[-1])
    for slot, cid in C.pools()[7]:
        for variant in ('hit', 'block'):
            for beat in range(blen):
                for late in (False, True):
                    run(slot, cid, variant, beat, late, stats)
    print('ticks watched', stats['ticks'], '| events fired', stats['fired'])
    print('dragon y range %.1f .. %.1f | farthest |x| or |z| %.1f | worst root->visible gap %.2f blocks' % (stats['ymin'], stats['ymax'], stats['far'], stats['lag']))
    for who, v in stats['clear'].items():
        print('min clearance above', who, ':', v)
    print('unknown/missing:', stats['bad'])
    worst = min(stats['clear']['steve'][0], stats['clear']['enderman'][0])
    print('RESULT:', 'OK' if worst >= NEED and not stats['bad'] else 'PROBLEM')

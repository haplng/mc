"""Force every card variant (hit / sweet-spot crit / countered) in every stage and check the game recovers."""
import sys, re
import os as _os; ROOT = _os.environ.get('EK_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/tools')
import sim as S
from sim import Sim, Ctx, Ent
from collections import Counter
OUT = ROOT + '/out/eokka'
calls = Counter(); orig = S.Sim.run_fn
def run_fn(self, name, ctx, args=None):
    calls[name] += 1
    return orig(self, name, ctx, args)
S.Sim.run_fn = run_fn

def pools():
    out = {}
    for n in range(1, 8):
        ids = []
        for line in open(f'{OUT}/data/ek/function/cards/use_s{n}.mcfunction'):
            m = re.search(r'matches (\d) run return run function ek:c/(\w+)/try', line)
            if m: ids.append((int(m.group(1)), m.group(2)))
        out[n] = ids
    return out

def setup(stage, seed=1):
    sm = Sim(OUT, seed=seed); sm.run_fn('load', Ctx())
    pl = Ent('player', (0.5, 57, 26.5)); sm.ents.append(pl)
    for _ in range(60): sm.step()
    sm.scores[('#runs', 'ek')] = 5; sm.scores[('#wins', 'ek')] = 5
    pl.data['slot'] = 0; sm.scores[(pl.id, 'ek.use')] = 1; sm.step()
    if stage > 1:
        sm.scores[('#stage', 'ek')] = stage; sm.run_fn('game/stage_begin', Ctx())
    return sm, pl

def hint(sm, pl, stage, slot):
    sm.scores[('#sl', 'ek')] = slot; sm.scores[('#hint', 'ek')] = 0
    sm.run_fn(f'ui/hint_s{stage}', Ctx(pl)); return sm.get('hint') == 1

def trial(stage, slot, cid, variant):
    sm, pl = setup(stage)
    if variant == 'block': sm.scores[('#l_' + cid, 'ek')] = 1
    fired = False; t_limit = 9000
    while sm.get('state') == 1 and sm.get('stage') == stage and sm.t < t_limit:
        ok = sm.get('intr') == 0 and sm.get('steve') == 1 and (sm.scores.get((pl.id, 'ek.cd'), 0) or 0) <= 0
        if ok:
            h = hint(sm, pl, stage, slot)
            want = (variant == 'crit' and h) or (variant == 'hit' and not h) or variant == 'block'
            if want:
                sm.scores[('#energy', 'ek')] = 100
                before = calls[f'ev/{cid}_{variant}/start']; cant = calls['cards/cant']
                pl.data['slot'] = slot; sm.scores[(pl.id, 'ek.use')] = 1; sm.step()
                if calls[f'ev/{cid}_{variant}/start'] > before: fired = True; break
                if calls['cards/cant'] == cant and sm.get('intr') != 0:
                    return f'WRONG VARIANT started (intr={sm.get("intr")})'
                continue
        sm.step()
    if not fired: return 'never possible (no window found)'
    key0 = (sm.get('stage'), sm.get('beat')); t0 = sm.t; ended_intr = None
    while sm.t - t0 < 6000:
        sm.step()
        if sm.get('state') != 1: return 'ok (game ended: res=%s)' % sm.get('res')
        if sm.get('intr') == 0 and ended_intr is None: ended_intr = sm.t - t0
        n_st = sum(1 for e in sm.ents if 'ek.steve' in e.tags)
        if ended_intr is not None and n_st != 1 and sm.get('steve') == 1: return f'steve count {n_st} after event'
        if ended_intr is not None and (sm.get('stage'), sm.get('beat')) != key0:
            left = [t for e in sm.ents for t in e.tags if t in ('ek.mob', 'ek.evt', 'ek.chase')]
            if sm.unknown or sm.missing: return 'unknown/missing: %s %s' % (dict(sm.unknown), dict(sm.missing))
            return 'ok (event %d ticks%s)' % (ended_intr, ', leftovers ' + str(Counter(left)) if left else '')
    return f'STALL after event: stage {sm.get("stage")} beat {sm.get("beat")} intr {sm.get("intr")} phase {sm.get("phase")} at {sm.get("at")}/{sm.get("alen")} steve {sm.get("steve")}'

if __name__ == '__main__':
    bad = 0
    for stage, ids in pools().items():
        for slot, cid in ids:
            row = []
            for variant in ('hit', 'crit', 'block'):
                r = trial(stage, slot, cid, variant); row.append(f'{variant}: {r}')
                if not r.startswith('ok'): bad += 1
            print(f's{stage} [{slot}] {cid:10s} | ' + ' | '.join(row))
    print('PROBLEMS:', bad)

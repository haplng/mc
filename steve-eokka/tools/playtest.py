"""Headless play-throughs of the generated datapack using the mini interpreter."""
import sys, random
import os as _os; ROOT = _os.environ.get('EK_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
from collections import Counter
sys.path.insert(0, ROOT + '/tools')
from sim import Sim, Ctx, Ent

OUT = ROOT + '/out/eokka'

def play(mode, seed=1, start_slot=0, unlock=False, verbose=False, max_ticks=60000, second_run=False):
    sim = Sim(OUT, seed=seed); rnd = random.Random(seed)
    sim.run_fn('load', Ctx())
    pl = Ent('player', (0.5, 57, 26.5)); sim.ents.append(pl)
    for _ in range(80): sim.step()
    assert sim.get('built') == 1, 'world never built'
    assert sim.get('state') == 0
    if unlock:
        sim.scores[('#runs', 'ek')] = 5; sim.scores[('#wins', 'ek')] = 5
    def press(slot):
        pl.data['slot'] = slot; sim.scores[(pl.id, 'ek.use')] = 1
    press(start_slot); sim.step()
    assert sim.get('state') == 1, 'game did not start'
    issues = []; marks = []; last = None; last_t = sim.t; maxent = 0; used = Counter(); t0 = sim.t
    minm = 999; stage_seen = set()
    while sim.get('state') == 1 and sim.t - t0 < max_ticks:
        st, bt, intr = sim.get('stage'), sim.get('beat'), sim.get('intr')
        stage_seen.add(st)
        key = (st, bt)
        if key != last:
            marks.append((sim.t - t0, st, bt)); last = key; last_t = sim.t
        if sim.t - last_t > 5000:
            issues.append(f'STALL at stage {st} beat {bt} intr {intr} phase {sim.get("phase")} at {sim.get("at")} steve {sim.get("steve")} t={sim.t - t0}')
            break
        n_steve = sum(1 for e in sim.ents if 'ek.steve' in e.tags)
        if n_steve > 1: issues.append(f'{n_steve} Steves at t={sim.t - t0}')
        maxent = max(maxent, len(sim.ents)); minm = min(minm, sim.get('mental'))
        if mode != 'none' and intr == 0 and sim.get('steve') == 1 and (sim.scores.get((pl.id, 'ek.cd'), 0) or 0) <= 0:
            e = sim.get('energy')
            if mode == 'random' and e >= 15 and rnd.random() < 0.04:
                sl = rnd.randint(0, 4); press(sl); used[(st, sl)] += 1
            elif mode == 'sweet' and e >= 15:
                for sl in rnd.sample(range(5), 5):
                    sim.scores[('#sl', 'ek')] = sl; sim.scores[('#hint', 'ek')] = 0
                    sim.run_fn(f'ui/hint_s{st}', Ctx(pl))
                    if sim.get('hint') == 1 and rnd.random() < 0.25:
                        press(sl); used[(st, sl)] += 1; break
            elif mode == 'spam' and e >= 15 and rnd.random() < 0.5:
                sl = rnd.randint(0, 4); press(sl); used[(st, sl)] += 1
        sim.step()
    dur = sim.t - t0
    res = {'mode': mode, 'seed': seed, 'ticks': dur, 'secs': dur / 20, 'state': sim.get('state'), 'res': sim.get('res'), 'stage': sim.get('stage'),
           'mental_min': minm, 'deaths': sim.get('deaths'), 'cards': sim.get('ncards'), 'total': sim.get('total'), 'day': sim.get('day'),
           'maxent': maxent, 'stages': sorted(x for x in stage_seen if x)}
    if sim.get('state') != 3: issues.append('game did not reach the result state')
    # result screen + back to lobby + optional second run
    for _ in range(200): sim.step()
    res['grade'] = sim.storage.get('r', {}).get('grade'); res['top'] = [sim.storage.get('r', {}).get(k) for k in ('t1', 'n1', 't2', 'n2', 't3', 'n3')]
    press(0); sim.step()
    if sim.get('state') != 0: issues.append('did not return to lobby')
    left = Counter(t for e in sim.ents for t in e.tags if e.type != 'player')
    res['lobby_entities'] = dict(left)
    if second_run:
        for _ in range(5): sim.step()
        press(0); sim.step()
        if sim.get('state') != 1: issues.append('second run did not start')
        for _ in range(600): sim.step()
        if sim.get('stage') != 1 or sim.get('beat') is None: issues.append('second run looks broken')
        res['second_beat'] = sim.get('beat')
    if sim.unknown: issues.append('unknown commands: ' + str(dict(sim.unknown)))
    if sim.missing: issues.append('missing functions: ' + str(dict(sim.missing)))
    return res, issues, marks, sim, used

if __name__ == '__main__':
    res, issues, marks, sim, _ = play('none', verbose=True, second_run=True)
    print('== no cards:', res)
    for i in issues: print('  ISSUE', i)
    prev = None
    for tt, st, bt in marks:
        if st != prev: print(f'  stage {st} starts at {tt / 20:.0f}s'); prev = st
    print('  --- story log (first run) ---')
    for tt, line in sim.log[:400]:
        if line and 'ISSUE' not in line: print(f'   [{tt / 20:6.1f}s] {line[:110]}')

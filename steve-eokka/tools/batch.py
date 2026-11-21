import sys
import os as _os; ROOT = _os.environ.get('EK_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/tools')
from playtest import play
from collections import Counter
allissues = Counter(); rows = []
for mode in ('random', 'sweet', 'spam'):
    for seed in range(1, 9):
        for slot in (0, 1, 2):
            if seed > 3 and slot != 0: continue
            try:
                res, issues, marks, sim, used = play(mode, seed=seed, start_slot=slot, unlock=True, second_run=(seed == 1))
            except Exception as ex:
                import traceback; traceback.print_exc(); allissues[f'EXC {mode} {seed} {slot}: {ex}'] += 1; continue
            rows.append((mode, seed, slot, res))
            for i in issues: allissues[f'[{mode} s{seed} d{slot}] {i}'] += 1
print(f'{len(rows)} games')
for mode in ('random', 'sweet', 'spam'):
    rs = [r for m, s, d, r in rows if m == mode]
    wins = sum(1 for r in rs if r['res'] == 1); n = len(rs)
    print(f"{mode:7s}: wins {wins}/{n}  avg secs {sum(r['secs'] for r in rs)/n:.0f}  avg cards {sum(r['cards'] or 0 for r in rs)/n:.0f}  avg deaths {sum(r['deaths'] or 0 for r in rs)/n:.1f}  avg dmg {sum(r['total'] or 0 for r in rs)/n:.0f}  maxent {max(r['maxent'] for r in rs)}  end stages {Counter(r['stage'] for r in rs)}")
for m, s, d, r in rows[:6] + rows[-3:]:
    print('  ', m, s, d, {k: r[k] for k in ('secs', 'res', 'stage', 'mental_min', 'deaths', 'cards', 'total', 'day', 'grade', 'top')})
print('ISSUES:', len(allissues))
for k, v in list(allissues.items())[:40]: print('  ', k)

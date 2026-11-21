"""Fire every card in every beat on the real 26.3 server and report what the server complains about.

The test server world carries a tiny helper datapack (`ekt`): at the first free tick of the chosen beat/phase it puts the
cursor at a chosen offset from Steve and uses the chosen card, exactly as a right-click would (cards/…/aim or …/try).

Usage: python3 tools/livecards.py [stage ...]
"""
import os, re, sys, time, collections
import os as _os; ROOT = _os.environ.get('EK_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live import Live

OUT = ROOT + '/out/eokka/data/ek/function'
BENIGN = ("Failed to encode value 'DYING' to field 'pose'", 'EntityStorage] Serialization errors', 'chunk@[',
          'authlib', 'minecraftservices', 'java.base/', 'Services Discovery')


def pools():
    res = {}
    for n in range(1, 8):
        ids = []
        for line in open(f'{OUT}/cards/use_s{n}.mcfunction'):
            m = re.search(r'matches (\d+) run return run function ek:c/(\w+)/(try|aim)$', line.strip())
            if m: ids.append((int(m.group(1)), m.group(2), m.group(3)))
        res[n] = ids
    return res


def blen(stage):
    for line in open(f'{OUT}/s{stage}/init.mcfunction'):
        if '#blen' in line: return int(line.split()[-1])
    return 0


def norm(line):
    line = re.sub(r'^\[[0-9:]+\] ', '', line)
    line = re.sub(r"/\d+, l=", '/N, l=', line)
    line = re.sub(r'-?\d+\.\d+', '#', line)
    return line[:300]


def one(L, stage, cid, fn, learned, beat, phase, dx=0.0):
    L.cmd('function ekt:goto {prev:%d}' % (stage - 1))
    if learned: L.cmd(f'scoreboard players set #l_{cid} ek 1')
    L.cmd('data modify storage ekt:s a set value {id:"%s",fn:"%s",dx:%s,dz:0}' % (cid, fn, dx))
    for k, v in (('beat', beat), ('phase', phase), ('arm', 1), ('now', 0), ('sweet', -1), ('ev', 0), ('tier', -1), ('cap', 0)):
        L.cmd(f'scoreboard players set #{k} ekt {v}')
    L.log()
    L.step(1800)
    arm = L.score('#arm', 'ekt')
    if arm == 1: return None            # that beat/phase never offered a free moment
    if arm == 2: L.step(700); arm = L.score('#arm', 'ekt')
    res = {'arm': arm, 'sweet': L.score('#sweet', 'ekt'), 'ev': L.score('#ev', 'ekt'), 'tier': L.score('#tier', 'ekt')}
    L.step(60)
    res.update(L.scores('state', 'stage', 'intr', 'steve', 'snap', 'drop'))
    res['steves'] = L.count('@e[tag=ek.steve]'); res['mobs'] = L.count('@e[tag=ek.mob]'); res['evt'] = L.count('@e[tag=ek.evt]')
    res['aimleft'] = L.count('@e[tag=ek.aim]') + L.count('@e[tag=ek.dropv]') + L.count('@e[tag=ek.ring]')
    res['log'] = [l for l in L.problems() if not any(b in l for b in BENIGN)]
    return res


def run(stages, quick=False):
    L = Live(); P = pools()
    problems = collections.Counter(); where = {}; cover = collections.Counter(); bad = []; tiers = collections.Counter()
    t0 = time.time(); runs = 0
    for stage in stages:
        nb = blen(stage)
        for slot, cid, fn in P[stage]:
            cases = []
            beats = range(nb) if not quick else range(0, nb, 3)
            for learned in (0, 1):
                for beat in beats: cases.append((learned, beat, 1, 0.0))
            if fn == 'aim':
                for beat in list(range(1, nb, max(1, nb // 3)))[:3]:
                    for dx in (1.8, 3.2, 12.0): cases.append((0, beat, 1, dx))
                    cases.append((0, beat, 0, 0.0)); cases.append((0, beat, 0, 1.5))
            for learned, beat, phase, dx in cases:
                r = one(L, stage, cid, fn, learned, beat, phase, dx)
                if r is None: continue
                runs += 1
                played = r['ev'] and r['ev'] > 0
                kind = 'block' if learned else ('crit' if r['sweet'] == 1 else 'hit')
                if fn == 'aim' and r['tier'] is not None and r['tier'] <= 1: kind = 'graze' if r['tier'] == 1 else 'miss'
                label = f's{stage} {cid}/{kind}@beat{beat}.{phase} dx={dx}'
                if fn == 'aim': tiers[(cid, phase, dx, r['tier'])] += 1
                if played: cover[(stage, cid, kind)] += 1
                elif fn == 'aim': cover[(stage, cid, kind)] += 1
                if r['arm'] != 3: bad.append((label, 'never ended', r))
                elif r['state'] == 1 and r['stage'] == stage:
                    if fn == 'aim' and r['tier'] is not None and r['tier'] >= 2 and not played: bad.append((label, 'hit without an event', r))
                    if fn == 'aim' and r['tier'] is not None and 0 <= r['tier'] <= 1 and played: bad.append((label, 'event on a miss', r))
                    if fn == 'try' and not played: bad.append((label, 'no event', r))
                    if r['intr'] == 0 and r['mobs']: bad.append((label, 'mobs left behind', r['mobs']))
                    if r['intr'] == 0 and r['evt']: bad.append((label, 'event marker left behind', r['evt']))
                    if r['intr'] == 0 and r['drop'] != 1 and r['aimleft']: bad.append((label, 'aim entities left behind', r['aimleft']))
                    if r['steve'] == 1 and r['steves'] != 1: bad.append((label, 'steve count', r['steves']))
                    if r['intr'] == 0 and r['snap'] != 1: bad.append((label, 'snap left off', r['snap']))
                for l in r['log']:
                    k = norm(l); problems[k] += 1; where.setdefault(k, label)
        print(f'stage {stage} done: {runs} card uses so far, {round(time.time() - t0)}s', flush=True)
    print('card uses', runs)
    print('coverage (stage, card): hit / crit / block / graze / miss')
    for st in stages:
        for slot, cid, fn in P[st]:
            print('  ', st, cid, fn, [cover[(st, cid, k)] for k in ('hit', 'crit', 'block', 'graze', 'miss')])
    print('tiers by (card, phase, dx):')
    agg = collections.defaultdict(collections.Counter)
    for (cid, phase, dx, tier), n in tiers.items(): agg[(cid, phase, dx)][tier] += n
    for k in sorted(agg): print('  ', k, dict(agg[k]))
    print('LOGIC PROBLEMS:', len(bad))
    for s in bad[:40]: print('  ', s)
    print('SERVER COMPLAINTS:', len(problems))
    for k, v in problems.most_common(40): print(f'  x{v}  [{where[k]}]  {k}')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != 'quick']
    stages = [int(a) for a in args] or list(range(1, 8))
    run(stages, quick='quick' in sys.argv)

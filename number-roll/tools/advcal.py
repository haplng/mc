# -*- coding: utf-8 -*-
"""도전과제 보상 맞추기: 시뮬레이터를 여러 번 돌려 '그 도전과제를 깰 즈음의 분당 수입'을 보고 보상을 제안한다.
  python3 advcal.py SIMDIR HOURS [NOADV]
   → 열쇠, 달성 시각(분, 가운데값), 그때 분당 수입(기하평균), 제안 보상, 지금 보상
"""
import math, os, subprocess, sys, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import adv as ADV
from common import won

simdir, hours = sys.argv[1], sys.argv[2]
env = dict(os.environ, TABLE='1')
if len(sys.argv) > 3:
    env['NOADV'] = '1'
runs = [(1.0, 1), (1.0, 2), (0.3, 3), (0.3, 4), (0.0, 5), (1.0, 6)]
procs = [subprocess.Popen([os.path.join(simdir, 'sim'), hours, str(a), str(s), '1'], stdout=subprocess.PIPE, text=True, env=env) for a, s in runs]
T, I = {}, {}
sections = {}
for (a, s), p in zip(runs, procs):
    out = p.communicate()[0]
    sec = None
    for ln in out.split('\n'):
        if ln.startswith('['):
            sec = ln[1:ln.index(']')]
            continue
        if ln.startswith('끝'):
            print('active %.1f seed %d: %s' % (a, s, ln[:200]))
        if sec == '도전과제' and ln.strip():
            f = ln.split()
            key, t = f[0], float(f[1])
            if t >= 0:
                inc = f[2]
                v = float(inc[:-1]) * {'만': 1e4, '억': 1e8, '조': 1e12}[inc[-1]] if inc[-1] in '만억조' else (float(inc) if inc != '-' else 0)
                T.setdefault(key, []).append(t)
                I.setdefault(key, []).append(max(v, 1500.0))
        elif sec in ('해금', '조커') and ln.strip():
            f = ln.split('분 값')
            name = f[0].rsplit(None, 1)[0].strip()
            t = float(f[0].rsplit(None, 1)[1])
            sections.setdefault(sec, {}).setdefault(name, []).append(t)


def nice(x):
    if x < 1000:
        return 500 if x < 750 else 1000
    e = int(math.floor(math.log10(x)))
    m = x / 10 ** e
    for c in (1, 1.5, 2, 3, 5, 7, 10):
        if m <= c * 1.15:
            return int(round(c * 10 ** e))
    return int(10 ** (e + 1))


F = {'task': 1.5, 'goal': 2.0, 'challenge': 3.0}
SUG = {}


def factor(t):
    # 초반엔 도전과제가 몰려 있어서 작게, 뒤로 갈수록 크게
    return 0.5 if t < 30 else (1.0 if t < 60 else 2.0)
print('\n%-11s %5s %9s %11s %11s %11s' % ('key', 'n', 'min', 'income', 'suggest', 'now'))
for a in ADV.A:
    k = a['key']
    if k in T:
        t = statistics.median(T[k])
        g = math.exp(sum(math.log(v) for v in I[k]) / len(I[k]))
        SUG[k] = nice(g * factor(t))
        print('%-11s %5d %9.1f %11s %11s %11s   %s' % (k, len(T[k]), t, won(int(g)), won(SUG[k]), won(a['reward'] or 0), a['title']))
    else:
        print('%-11s %5d %9s %11s %11s %11s   %s' % (k, 0, '-', '-', '?', won(a['reward'] or 0), a['title']))
for sec in sections:
    print('\n[%s] 달성 시각(분): 가운데값 (가장 빠름 ~ 가장 늦음)' % sec)
    for name, ts in sections[sec].items():
        ok = [t for t in ts if t >= 0]
        print('  %-22s %s' % (name, ('%7.1f (%.0f ~ %.0f)%s' % (statistics.median(ok), min(ok), max(ok), '' if len(ok) == len(ts) else '  ※ %d번은 못 감' % (len(ts) - len(ok)))) if ok else '-'))

if os.environ.get('SUGOUT'):
    import json
    json.dump(SUG, open(os.environ['SUGOUT'], 'w'))

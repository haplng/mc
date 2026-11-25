# -*- coding: utf-8 -*-
"""count 결과(JSON 여러 개)를 합쳐 족보별 확률·등급·코인을 정한다 → src/tiers.json
  python3 mktiers.py OUT.json c_a.json c_b.json ...
"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import hands as HM

def nice(x):
    """유효숫자 2자리로 반올림"""
    if x < 10:
        return max(1, int(round(x)))
    import math
    e = int(math.floor(math.log10(x))) - 1
    return int(round(x / 10 ** e) * 10 ** e)

def tier_of(inv):
    return 0 if inv < 30 else 1 if inv < 300 else 2 if inv < 3000 else 3 if inv < 30000 else 4 if inv < 300000 else 5

out = sys.argv[1]
tot = 0
cnt = {}
ex = {}
nh = [0] * 64
for f in sys.argv[2:]:
    r = json.load(open(f))
    tot += r['total']
    for k, v in r['cnt'].items():
        cnt[k] = cnt.get(k, 0) + v[0]
        if v[0] and k not in ex:
            ex[k] = v[1]
    nh = [a + b for a, b in zip(nh, r['nh'])]
res = {}
for h in HM.HANDS:
    k = h['key']
    if h['eng'] and h['eng'][0] == 'alias':
        continue
    c = cnt[k]
    assert c > 0, k
    inv = tot / c
    res[k] = dict(count=c, inv=inv, tier=tier_of(inv), pay=nice(2 * inv), ex=ex[k])
json.dump(dict(total=tot, hands=res, nh=nh), open(out, 'w'), ensure_ascii=False, indent=0)
from collections import Counter
print(tot, Counter(v['tier'] for v in res.values()), len(res))
print('avg nh', sum(i * n for i, n in enumerate(nh)) / tot, 'zero', nh[0] / tot)

# -*- coding: utf-8 -*-
"""족보 목록 문서 만들기:  python3 handsdoc.py DIST_DIR/hands.json OUT.md"""
import json, sys
HI = json.load(open(sys.argv[1], encoding='utf-8'))
TN = ['흔함', '보통', '희귀', '영웅', '전설', '신화']


def inv(x):
    x = round(x)
    if x >= 10 ** 8: return '%.1f억' % (x / 1e8)
    if x >= 10 ** 4: return '%s만' % ('%.1f' % (x / 1e4)).rstrip('0').rstrip('.')
    return '{:,}'.format(x)


L = ['# 족보 %d개' % len(HI), '', '숫자 9자리 안에서 찾는 무늬들. 코인은 대략 `2 ÷ 확률` 이고, 같은 족보를 많이 뽑아 별(★)이 오르면 25%씩 더 받아.', '']
L.append('| 등급 | 개수 | 확률 |')
L.append('| --- | --- | --- |')
for t in range(6):
    hs = [h for h in HI if h['tier'] == t]
    L.append('| %s | %d | 1/%s ~ 1/%s |' % (TN[t], len(hs), inv(min(h['inv'] for h in hs)), inv(max(h['inv'] for h in hs))))
for t in range(6):
    hs = [h for h in HI if h['tier'] == t]
    L += ['', '## %s (%d개)' % (TN[t], len(hs)), '', '| # | 족보 | 조건 | 확률 | 코인 |', '| --- | --- | --- | --- | --- |']
    for h in hs:
        L.append('| %d | **%s** | %s | 1/%s | %s |' % (h['id'], h['name'], h['rule'].replace('|', '/'), inv(h['inv']), '{:,}'.format(h['pay'])))
open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print(len(HI), 'hands')

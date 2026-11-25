# -*- coding: utf-8 -*-
"""hands.py → 기준 구현 C 코드(ref_hands.h)를 만든다.

  python3 refgen.py OUT.h [tiers.json]

묶음(grp) 규칙: 같은 묶음에서는 '뒤에 적힌(더 높은)' 족보부터 보고, 처음으로 raw가 참이면서
잠겨 있지 않은 족보 하나만 걸린다. alias 항목은 다른 족보의 또 다른 조건일 뿐이다.
"""
import json
import re
import sys

import hands as HM


def fast(expr):
    """HAS("a|b") 를 창문 정수 비교로 바꿔 빠르게 한다 (뜻은 같다)."""
    def rep(m):
        parts = m.group(1).split('|')
        return '(' + ' || '.join('HW(%d,%d)' % (len(p), int(p)) for p in parts) + ')'
    return re.sub(r'HAS\("([0-9|]+)"\)', rep, expr)


def build(tiers=None):
    hs = HM.HANDS
    idx = {h['key']: i for i, h in enumerate(hs)}
    out = []
    out.append('// 자동 생성 — refgen.py')
    out.append('#define NHAND %d' % len(hs))
    for h in hs:
        out.append('static int raw_%s(const X *x) { return (%s) != 0; }' % (h['key'], fast(h['raw'])))
        out.append('static int mk_%s(const X *x) { return (%s); }' % (h['key'], h['mk']))
    out.append('static const char *KEY[NHAND] = {%s};' % ', '.join('"%s"' % h['key'] for h in hs))
    # 잠금: tier 4(전설)는 ul4, tier 5(신화)는 ul5가 있어야 걸린다
    if tiers is None:
        tl = [0] * len(hs)
    else:
        tl = [tiers.get(h['key'], 0) for h in hs]
    for i, h in enumerate(hs):  # alias는 대상의 등급을 따른다
        if h['eng'] and h['eng'][0] == 'alias':
            tl[i] = tl[idx[h['eng'][1]]]
    out.append('static const int TIER[NHAND] = {%s};' % ', '.join(map(str, tl)))
    out.append('#define OPEN(i) (TIER[i] < 4 || (TIER[i] == 4 && ul4) || (TIER[i] == 5 && ul5))')
    out.append('static void detect(const X *x, unsigned char *hit, int ul4, int ul5) {')
    out.append('  memset(hit, 0, NHAND);')
    groups = {}
    order = []
    for i, h in enumerate(hs):
        g = h['grp']
        if g is None:
            tgt = i
            out.append('  if (OPEN(%d) && raw_%s(x)) hit[%d] = 1;' % (i, h['key'], tgt))
        else:
            if g not in groups:
                groups[g] = []
                order.append(g)
            groups[g].append(i)
    for g in order:
        mem = groups[g]
        out.append('  // 묶음 %s' % g)
        first = True
        for i in reversed(mem):
            h = hs[i]
            tgt = idx[h['eng'][1]] if (h['eng'] and h['eng'][0] == 'alias') else i
            out.append('  %sif (OPEN(%d) && raw_%s(x)) hit[%d] = 1;' % ('' if first else 'else ', i, h['key'], tgt))
            first = False
    out.append('}')
    out.append('static int marks(const X *x, int i) {')
    out.append('  switch (i) {')
    for i, h in enumerate(hs):
        if h['eng'] and h['eng'][0] == 'alias':
            continue
        # alias가 가리키는 족보는 두 조건의 자리 표시를 합친다
        al = [a for a in hs if a['eng'] and a['eng'][0] == 'alias' and a['eng'][1] == h['key']]
        e = 'mk_%s(x)' % h['key']
        for a in al:
            e += ' | mk_%s(x)' % a['key']
        out.append('    case %d: return %s;' % (i, e))
    out.append('  }')
    out.append('  return 0;')
    out.append('}')
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    tiers = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
    open(sys.argv[1], 'w').write(build(tiers))

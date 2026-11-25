# -*- coding: utf-8 -*-
"""코인 계산(roll/coins, 조커, sys/addc2, sys/afford, sys/spend, ms/rel)을 C로 옮겨 식 그대로 계산한 값과 비교한다.

  python3 cointest.py DIST_DIR WORKDIR      (DIST_DIR: build.py 가 만든 dice_roll 폴더)
  → WORKDIR/cointest 를 만들어 돌린다
"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)
import mc2c
from jokers import JOKERS

root, work = sys.argv[1], sys.argv[2]
F = {}
for sub in ('roll', 'joker', 'sys', 'ms', 'stats'):
    F.update(mc2c.load_dir(root, 'jb', sub))
ROOTS = ['jb:roll/coins', 'jb:sys/addc', 'jb:sys/addc2', 'jb:sys/afford', 'jb:sys/spend', 'jb:ms/rel', 'jb:stats/earn']
need, todo = set(), list(ROOTS)
while todo:
    p = todo.pop()
    if p in need or p not in F:
        continue
    need.add(p)
    for ln in F[p]:
        i = ln.find('function jb:')
        while i >= 0:
            q = ln[i + 9:].split(' ')[0]
            todo.append(q)
            i = ln.find('function jb:', i + 1)
t = mc2c.T()
for p in sorted(need):
    assert not any(l.strip().startswith('$') for l in F[p]), p
    t.add(p, F[p])
code, missing = t.emit()
assert not missing, missing
L = [code]
L.append('#include <stdlib.h>\n#include <math.h>')
L.append('static unsigned long long RS = 88172645463325252ULL;')
L.append('static unsigned long long rnd(void) { RS ^= RS << 13; RS ^= RS >> 7; RS ^= RS << 17; return RS; }')
L.append('static int ri(int lo, int hi) { return lo + (int)(rnd() % (unsigned long long)(hi - lo + 1)); }')
L.append('static int rlog(double mx) { double u = (rnd() % 1000000) / 1e6; return (int)pow(mx, u); }')
L.append('int main(void) {')
L.append('  long bad = 0, N = 3000000; double worst = 0;')
for c in (2, 3, 4, 5, 7, 10, 20, 25, 50, 100, 1000, 10000, 1000000, 1000000000, 100000000, 2000, 700000):
    if ('G_c%d__jv' % c) in t.vars:
        L.append('  G_c%d__jv = %d;' % (c, c))
# 상수 전부
for v in sorted(t.vars):
    if v.startswith('G_c') and v.endswith('__jv') and v[3:-4].isdigit():
        L.append('  %s = %s;' % (v, v[3:-4]))
L.append('  for (long it = 0; it < N; it++) {')
L.append('    int p0 = ri(0, 3) ? rlog(3000) : 0, p1 = ri(0, 2) ? rlog(60000) : 0, p2 = ri(0, 1) ? rlog(500000) : 0, p3 = ri(0, 3) ? 0 : rlog(ri(0, 3) ? 3e6 : 2e8);')
L.append('    int tot = p0 + p1 + p2 + p3;')
L.append('    int fs = ri(0, tot), fst = ri(0, tot - fs), fm = ri(0, tot - fs - fst), fw = ri(0, tot - fs - fst - fm);')
L.append('    int nh = tot ? ri(1, ri(0, 5) ? 12 : 30) : 0, man = ri(0, 1), e1 = ri(0, 5), e2 = ri(0, 5), u4 = ri(0, 10);')
L.append('    int found = ri(0, 400), stot = ri(0, 2000), cdig = ri(1, 16), q7 = ri(0, 9), q0 = ri(0, 9 - q7), nt = ri(1, 6);')
L.append('    G_p0__jv = p0; G_p1__jv = p1; G_p2__jv = p2; G_p3__jv = p3; G_pay__jv = tot; G_nh__jv = nh; G_man__jv = man;')
L.append('    G_pf_same__jv = fs; G_pf_stair__jv = fst; G_pf_mirror__jv = fm; G_pf_word__jv = fw; G_cdig__jv = cdig;')
L.append('    G_gen__jv = 77; G_t0__jv = G_t1__jv = G_t2__jv = G_t3__jv = G_t4__jv = G_t5__jv = 0;')
L.append('    { int k = 0; int *tp[6] = {&G_t0__jv, &G_t1__jv, &G_t2__jv, &G_t3__jv, &G_t4__jv, &G_t5__jv}; while (k < nt) { int j = ri(0, 5); if (*tp[j] != 77) { *tp[j] = 77; k++; } } }')
L.append('    P__jb_e1 = e1; P__jb_e2 = e2; P__jb_u4 = u4; P__jb_found = found; P__jb_stot = stot;')
for d in (7, 0):
    if ('G_q%d__jv' % d) in t.vars:
        L.append('    G_q%d__jv = q%d;' % (d, d))
L.append('    int jq = 0, eq[%d] = {0};' % (len(JOKERS) + 1))
L.append('    { int want = ri(0, 4); while (jq < want) { int j = ri(1, %d); if (!eq[j]) { eq[j] = 1; jq++; } } }' % len(JOKERS))
for j in JOKERS:
    if ('P__jb_j%d' % j['id']) in t.vars:
        L.append('    P__jb_j%d = eq[%d] ? 2 : ri(0, 1);' % (j['id'], j['id']))
L.append('    P__jb_jeq = jq;')
# 기준 계산
L.append('    double a0 = p0, a1 = p1, a2 = p2, a3 = p3, ax = 0;')
for j in JOKERS:
    k = j['kind']
    if k[0] != 'part':
        continue
    c = {'p0': 'a0 *= %d;' % k[2], 'p12': 'a1 *= %d; a2 *= %d;' % (k[2], k[2]), 'p3': 'a3 *= %d;' % k[2],
         'same': 'ax += %d.0 * fs;' % (k[2] - 1), 'stair': 'ax += %d.0 * fst;' % (k[2] - 1), 'mirror': 'ax += %d.0 * fm;' % (k[2] - 1),
         'word': 'ax += %d.0 * fw;' % (k[2] - 1)}[k[1]]
    L.append('    if (eq[%d]) { %s }' % (j['id'], c))
L.append('    double pay = a0 + a1 + a2 + a3 + ax, v = pay + (a2 + a3) * e1 * 0.5 + (nh >= 2 ? pay * (nh - 1) * e2 * 0.1 : 0);')
for j in JOKERS:
    k = j['kind']
    if k[0] in ('part', 'mission'):
        continue
    m = {'digit': lambda: '100 + q%d * %d' % (k[1], k[2]), 'nh_le': lambda: 'nh <= %d ? %d : 100' % (k[1], k[2]),
         'nh_ge': lambda: 'nh >= %d ? %d : 100' % (k[1], k[2]), 'tiers': lambda: 'nt >= %d ? %d : 100' % (k[1], k[2]),
         'manual': lambda: 'man ? %d : 100' % k[1], 'auto': lambda: 'man ? 100 : %d' % k[1],
         'found': lambda: '100 + found / %d * %d' % (k[1], k[2]), 'stars': lambda: '100 + stot / %d * %d' % (k[1], k[2]),
         'cdig': lambda: '100 + cdig * %d' % k[1]}[k[0]]()
    L.append('    if (eq[%d]) { double m = %s; v = v * m / 100.0; }' % (j['id'], m))
L.append('    v *= 1 + u4 * 0.5; if (v > 2e12) v = 2e12;')
L.append('    f_jb_roll_coins();')
L.append('    double got = G_rth__jv * 1e9 + G_rtl__jv;')
L.append('    double err = fabs(got - v), tol = v * 0.004 + 1.5;')
L.append('    int okrt = (G_rth__jv >= 2) ? (G_rt__jv == 2000000000) : (G_rt__jv == G_rth__jv * 1000000000 + G_rtl__jv);')
L.append('    if (err > tol || G_rtl__jv < 0 || G_rtl__jv >= 1000000000 || G_rth__jv < 0 || !okrt || G_pay0__jv != tot) {')
L.append('      if (bad < 12) printf("BAD p=%d/%d/%d/%d f=%d/%d/%d/%d nh=%d e1=%d e2=%d u4=%d man=%d jq=%d  want %.0f got %.0f (rth %d rtl %d rt %d ku %d)\\n", p0, p1, p2, p3, fs, fst, fm, fw, nh, e1, e2, u4, man, jq, v, got, G_rth__jv, G_rtl__jv, G_rt__jv, G_ku__jv);')
L.append('      bad++; }')
L.append('    if (v > 100 && err / v > worst) worst = err / v;')
L.append('  }')
L.append('  printf("roll/coins: %ld cases, bad %ld, worst relative error %.4f%%\\n", N, bad, worst * 100);')
# 코인 더하기·빼기·비교
L.append('''
  long bad2 = 0;
  for (long it = 0; it < 2000000; it++) {
    long long c = ri(0, 3) ? (long long)rlog(2e9) : (long long)ri(0, 2000000) * 1000000000LL + ri(0, 999999999);
    long long add = ri(0, 2) ? rlog(2.1e9) : (long long)ri(0, 5000) * 1000000000LL + ri(0, 999999999);
    P__jb_coins = (int)(c % 1000000000LL); P__jb_cb = (int)(c / 1000000000LL);
    if (add < 2100000000LL && ri(0, 1)) { G_cg__jv = (int)add; f_jb_sys_addc(); }
    else { G_cgh__jv = (int)(add / 1000000000LL); G_cgl__jv = (int)(add % 1000000000LL); f_jb_sys_addc2(); }
    long long want = c + add; if (want >= 10000000LL * 1000000000LL) want = 9999999LL * 1000000000LL + 999999999;
    long long got = (long long)P__jb_cb * 1000000000LL + P__jb_coins;
    if (got != want || P__jb_coins < 0 || P__jb_coins > 999999999) { if (bad2 < 5) printf("ADD bad %lld + %lld = %lld got %lld\\n", c, add, want, got); bad2++; }
    // 값 치르기
    long long price = ri(0, 2) ? rlog(1e9) : (long long)ri(0, 3000) * 1000000000LL + ri(0, 999999999);
    G_costb__jv = (int)(price / 1000000000LL); G_cost__jv = (int)(price % 1000000000LL);
    f_jb_sys_afford();
    if ((G_ok__jv == 1) != (got >= price)) { if (bad2 < 5) printf("AFFORD bad have %lld price %lld ok %d\\n", got, price, G_ok__jv); bad2++; }
    if (got >= price) { f_jb_sys_spend(); long long g2 = (long long)P__jb_cb * 1000000000LL + P__jb_coins;
      if (g2 != got - price || P__jb_coins < 0 || P__jb_coins > 999999999) { if (bad2 < 5) printf("SPEND bad %lld - %lld got %lld\\n", got, price, g2); bad2++; } }
  }
  printf("addc/afford/spend: bad %ld\\n", bad2);
  // 미션 보상 (숫자 하나 평균 수입의 K배)
  long bad3 = 0;
  for (long it = 0; it < 2000000; it++) {
    long long rc = ri(0, 2) ? (long long)rlog(1e9) : (long long)ri(0, 3000) * 1000000000LL + ri(0, 999999999);
    int rr = ri(0, 20) ? ri(1, 6000) : 0, K = (int[]){30, 300, 3000}[ri(0, 2)], base = ri(1, 24000000);
    P__jb_rc = (int)(rc % 1000000000LL); P__jb_rch = (int)(rc / 1000000000LL); P__jb_rr = rr;
    G_mrh__jv = 0; G_mrl__jv = base; G_mk__jv = K;
    f_jb_ms_rel();
    double got = G_mrh__jv * 1e9 + G_mrl__jv;
    double rcc = rc > 2000LL * 1000000000LL + 999999999 ? 2000e9 : (double)rc;
    double q = rr ? rcc / rr : 0; if (q > 700000e3) q = 700000e3;
    double want = q * K; if (want < base) want = base;
    if (fabs(got - want) > want * 0.01 + 3100 || G_mrl__jv < 0 || G_mrl__jv > 999999999) { if (bad3 < 8) printf("MS bad rc %lld rr %d K %d base %d want %.0f got %.0f\\n", rc, rr, K, base, want, got); bad3++; }
  }
  printf("ms/rel: bad %ld\\n", bad3);
  return bad || bad2 || bad3 ? 1 : 0;
}''')
os.makedirs(work, exist_ok=True)
open(os.path.join(work, 'cointest.c'), 'w').write('\n'.join(L))
r = subprocess.run(['gcc', '-O1', '-fwrapv', '-o', os.path.join(work, 'cointest'), os.path.join(work, 'cointest.c'), '-lm'], capture_output=True, text=True)
if r.returncode:
    print(r.stderr[:3000])
    sys.exit(1)
sys.exit(subprocess.run([os.path.join(work, 'cointest')]).returncode)

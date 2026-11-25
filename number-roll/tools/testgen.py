# -*- coding: utf-8 -*-
"""엔진을 C로 옮겨 기준 구현과 비교하는 시험 프로그램을 만든다.
  python3 testgen.py WORKDIR [tiers.json]
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))
import hands as HM
import engine as EM
import refgen
import mc2c

work = sys.argv[1]
tiers = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
if 'hands' in tiers:
    tiers = tiers['hands']
tier = {h['key']: tiers.get(h['key'], {}).get('tier', 0) if isinstance(tiers.get(h['key']), dict) else tiers.get(h['key'], 0) for h in HM.HANDS}
pay = {h['key']: (tiers.get(h['key'], {}).get('pay', 1) if isinstance(tiers.get(h['key']), dict) else 1) for h in HM.HANDS}
eng = EM.Engine(HM.HANDS, tier)
eng.build_eval()
eng.build_hits(pay)
if hasattr(eng, 'build_marks'):
    eng.build_marks()
t = mc2c.T()
t.var('#ul4', 'jv'); t.var('#ul5', 'jv'); t.var('#ml', 'jv')
for _i in range(1, 10): t.var('#lc%d' % _i, 'jv')
for path, lines in eng.F.items():
    if path.startswith('hand/c/'):
        continue
    t.add('jb:' + path, lines)
code, missing = t.emit()
missing = [m for m in missing if not m.startswith('jb:hand/c/')]
if missing:
    print('MISSING', missing)
open(os.path.join(work, 'eng.c'), 'w').write(code)
open(os.path.join(work, 'ref_hands.h'), 'w').write(refgen.build({k: tier[k] for k in tier}))
# 시험 본체
real = [h for h in HM.HANDS if not (h['eng'] and h['eng'][0] == 'alias')]
L = []
L.append('#include "eng.c"')
L.append('#include "ref.h"')
L.append('#include "ref_hands.h"')
L.append('static int *GP[NHAND] = {%s};' % ', '.join(('&G_g%d__jv' % eng.ids[h['key']]) if not (h['eng'] and h['eng'][0] == 'alias') else '0' for h in HM.HANDS))
L.append('static const int EID[NHAND] = {%s};' % ', '.join(str(eng.ids[h['key']]) if not (h['eng'] and h['eng'][0] == 'alias') else '0' for h in HM.HANDS))
consts = sorted(eng.consts)
L.append('static void consts(void) { %s }' % ' '.join('G_c%d__jv = %d;' % (c, c) for c in consts))
has_marks = hasattr(eng, 'build_marks')
L.append('''
static void setd(int n) { int t = n;
  G_d9__jv = t % 10; t /= 10; G_d8__jv = t % 10; t /= 10; G_d7__jv = t % 10; t /= 10; G_d6__jv = t % 10; t /= 10; G_d5__jv = t % 10; t /= 10;
  G_d4__jv = t % 10; t /= 10; G_d3__jv = t % 10; t /= 10; G_d2__jv = t % 10; t /= 10; G_d1__jv = t % 10; }
int main(int argc, char **argv) {
  long lo = 0, hi = 0, step = 1; FILE *fin = 0;
  if (argv[1][0] == '@') { fin = fopen(argv[1] + 1, "r"); hi = 2000000000; } else { lo = atol(argv[1]); hi = atol(argv[2]); step = atol(argv[3]); }
  int ul4 = argc > 4 ? atoi(argv[4]) : 1, ul5 = argc > 5 ? atoi(argv[5]) : 1;
  int mkevery = argc > 6 ? atoi(argv[6]) : 0;
  consts(); G_gen__jv = 1;
  unsigned char hit[NHAND]; X x; long bad = 0, tot = 0, mbad = 0, mchk = 0; long badh[NHAND]; memset(badh, 0, sizeof badh);
  static long mbadh[NHAND];
  long cmd0 = 0, cmdsum = 0, nhs = 0;
  for (long n = lo; n < hi; n += step) {
    if (fin) { int v; if (fscanf(fin, "%d", &v) != 1) break; n = v; }
    prep(&x, (int)n); detect(&x, hit, ul4, ul5); tot++;
    setd((int)n); G_ul4__jv = ul4; G_ul5__jv = ul5;
    cmd0 = CMDS; f_jb_hand_eval(); cmdsum += CMDS - cmd0;
    int nh = 0, ok = 1;
    for (int i = 0; i < NHAND; i++) { if (!GP[i]) continue; int e = (*GP[i] == G_gen__jv); if (e != hit[i]) { ok = 0; badh[i]++; if (badh[i] <= 3) printf("MISMATCH %09ld %s ref=%d eng=%d\\n", n, KEY[i], hit[i], e); } nh += hit[i]; }
    if (ok && nh != G_nh__jv) { ok = 0; if (bad < 20) printf("NH %09ld ref=%d eng=%d\\n", n, nh, G_nh__jv); }
    if (!ok) bad++;
    nhs += nh;
''')
if has_marks:
    L.append('''
    if (mkevery && ok) {
      int did = 0;
      for (int i = 0; i < NHAND; i++) { if (!GP[i] || !hit[i]) continue;
        if (!(TIER[i] >= 3 || tot % mkevery == 0)) continue;
        if (!did) { f_jb_hand_mprep(); did = 1; }
        G_lc1__jv = G_lc2__jv = G_lc3__jv = G_lc4__jv = G_lc5__jv = G_lc6__jv = G_lc7__jv = G_lc8__jv = G_lc9__jv = 0; G_ml__jv = 1;
        f_jb_hand_mk_clr(); MARK(EID[i]); f_jb_hand_mk_merge();
        int m = G_lc1__jv | G_lc2__jv << 1 | G_lc3__jv << 2 | G_lc4__jv << 3 | G_lc5__jv << 4 | G_lc6__jv << 5 | G_lc7__jv << 6 | G_lc8__jv << 7 | G_lc9__jv << 8;
        int r = marks(&x, i); mchk++;
        if (m != r) { mbad++; mbadh[i]++; if (mbadh[i] <= 3) printf("MARK %09ld %s ref=%d eng=%d\\n", n, KEY[i], r, m); }
      }
    }
''')
L.append('''
  }
  printf("total %ld bad %ld  marks checked %ld bad %ld  avg cmds %.1f  avg nh %.2f\\n", tot, bad, mchk, mbad, (double)cmdsum / tot, (double)nhs / tot);
  return bad || mbad ? 1 : 0;
}
''')
src = '\n'.join(L)
if has_marks:
    sw = 'static void MARK(int id) { switch (id) {\n' + '\n'.join('  case %d: f_jb_hand_m_%d(); break;' % (eng.ids[h['key']], eng.ids[h['key']]) for h in real) + '\n} }\n'
    src = src.replace('static void setd(int n)', sw + 'static void setd(int n)')
open(os.path.join(work, 'engtest.c'), 'w').write(src)
print('functions', len(eng.F), 'lines', sum(len(v) for v in eng.F.values()))

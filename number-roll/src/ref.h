// 숫자 굴리기 — 족보 기준 구현 (reference)
// 9자리 숫자 하나에 대해 "이 족보가 걸리는가 / 어느 자리가 빛나는가"를 가장 단순한 방식으로 계산한다.
// 데이터팩(mcfunction) 엔진은 이것과 따로 만들고, 10^9개 전부를 서로 비교해서 검증한다.
#include <string.h>
#include <stdlib.h>

typedef struct {
  int n;
  int d[9], e[8];
  int c[10];
  int mx, nd, sum, mn, mxd;
  int nr, rs[9], rl[9], rv[9];
  int MRv, NR2v, NR3v, NR4v;
  int w[10][9];  // w[L][i] = i번째부터 L자리 수
} X;

static int SEEN2[100], SEEN3[1000], SEEN4[10000], SEENG = 0;
static inline int span(int s, int l) { return ((1 << l) - 1) << s; }
#define ALL9 511

static void prep(X *x, int n) {
  x->n = n;
  int t = n;
  for (int i = 8; i >= 0; i--) { x->d[i] = t % 10; t /= 10; }
  for (int i = 0; i < 8; i++) x->e[i] = x->d[i + 1] - x->d[i];
  for (int v = 0; v < 10; v++) x->c[v] = 0;
  x->sum = 0; x->mn = 9; x->mxd = 0;
  for (int i = 0; i < 9; i++) {
    x->c[x->d[i]]++; x->sum += x->d[i];
    if (x->d[i] < x->mn) x->mn = x->d[i];
    if (x->d[i] > x->mxd) x->mxd = x->d[i];
  }
  x->mx = 0; x->nd = 0;
  for (int v = 0; v < 10; v++) { if (x->c[v] > x->mx) x->mx = x->c[v]; if (x->c[v]) x->nd++; }
  x->nr = 0;
  for (int i = 0; i < 9;) {
    int j = i; while (j < 9 && x->d[j] == x->d[i]) j++;
    x->rs[x->nr] = i; x->rl[x->nr] = j - i; x->rv[x->nr] = x->d[i]; x->nr++; i = j;
  }
  for (int i = 0; i < 9; i++) x->w[1][i] = x->d[i];
  for (int L = 2; L <= 9; L++) for (int i = 0; i + L <= 9; i++) x->w[L][i] = x->w[L - 1][i] * 10 + x->d[i + L - 1];
  SEENG++;
  for (int i = 0; i < 8; i++) SEEN2[x->w[2][i]] = SEENG;
  for (int i = 0; i < 7; i++) SEEN3[x->w[3][i]] = SEENG;
  for (int i = 0; i < 6; i++) SEEN4[x->w[4][i]] = SEENG;
  x->MRv = 0; x->NR2v = x->NR3v = x->NR4v = 0;
  for (int j = 0; j < x->nr; j++) {
    if (x->rl[j] > x->MRv) x->MRv = x->rl[j];
    if (x->rl[j] >= 2) x->NR2v++;
    if (x->rl[j] >= 3) x->NR3v++;
    if (x->rl[j] >= 4) x->NR4v++;
  }
}

#define D(i) (x->d[i])
#define E(i) (x->e[i])
#define C(v) (x->c[v])
#define MX (x->mx)
#define ND (x->nd)
#define SUM (x->sum)
#define MN (x->mn)
#define MXD (x->mxd)
#define MR (x->MRv)
#define NR2 (x->NR2v)
#define NR3 (x->NR3v)
#define NR4 (x->NR4v)
#define NRUN (x->nr)
#define RL(j) (x->rl[j])

// ---------- 조각(fragment) ----------
static int matchat(const X *x, const char *s, int L, int i) {
  for (int k = 0; k < L; k++) if (x->d[i + k] != s[k] - '0') return 0;
  return 1;
}
static int fpos(const X *x, const char *s) {  // 가장 왼쪽 위치(1부터), 없으면 0
  int L = (int)strlen(s);
  for (int i = 0; i + L <= 9; i++) if (matchat(x, s, L, i)) return i + 1;
  return 0;
}
// "a|b|c" 중 가장 왼쪽 (같은 자리면 앞에 적힌 것)
static int fposany(const X *x, const char *list, int *len) {
  int best = 0, bl = 0;
  const char *p = list;
  while (*p) {
    const char *q = p; while (*q && *q != '|') q++;
    char buf[12]; int L = (int)(q - p); memcpy(buf, p, L); buf[L] = 0;
    int f = fpos(x, buf);
    if (f && (!best || f < best)) { best = f; bl = L; }
    p = *q ? q + 1 : q;
  }
  if (len) *len = bl;
  return best;
}
static int has(const X *x, const char *list) { return fposany(x, list, 0) > 0; }
static int mhas(const X *x, const char *list) { int L; int f = fposany(x, list, &L); return f ? span(f - 1, L) : 0; }
static int starts(const X *x, const char *s) { return matchat(x, s, (int)strlen(s), 0); }
static int ends(const X *x, const char *s) { int L = (int)strlen(s); return matchat(x, s, L, 9 - L); }
static int occ(const X *x, const char *s) {  // 안 겹치게 왼쪽부터 센 개수
  int L = (int)strlen(s), n = 0;
  for (int i = 0; i + L <= 9;) { if (matchat(x, s, L, i)) { n++; i += L; } else i++; }
  return n;
}
static int mall(const X *x, const char *s) {  // 나온 곳 전부
  int L = (int)strlen(s), m = 0;
  for (int i = 0; i + L <= 9; i++) if (matchat(x, s, L, i)) m |= span(i, L);
  return m;
}
static int hw(const X *x, int L, int v) {
  if (L == 2) return SEEN2[v] == SEENG;
  if (L == 3) return SEEN3[v] == SEENG;
  if (L == 4) return SEEN4[v] == SEENG;
  for (int i = 0; i + L <= 9; i++) if (x->w[L][i] == v) return 1;
  return 0;
}
#define HW(L, v) hw(x, L, v)
#define HAS(s) has(x, s)
#define MHAS(s) mhas(x, s)
#define STARTS(s) starts(x, s)
#define ENDS(s) ends(x, s)
#define OCC(s) occ(x, s)
#define MALL(s) mall(x, s)

// ---------- 옆 숫자 차이로 보는 연속 ----------
static int lrun_e(const X *x, int lo, int hi) {  // e가 [lo,hi]인 칸이 이어지는 가장 긴 길이(자리 수)
  int best = 1, cur = 1;
  for (int i = 0; i < 8; i++) { if (x->e[i] >= lo && x->e[i] <= hi) { cur++; if (cur > best) best = cur; } else cur = 1; }
  return best;
}
static int mrun_e(const X *x, int lo, int hi, int k) {  // 길이 k 창문 중 전부 만족하는 것들의 합집합
  int m = 0;
  for (int p = 0; p + k <= 9; p++) {
    int ok = 1;
    for (int i = p; i < p + k - 1; i++) if (x->e[i] < lo || x->e[i] > hi) { ok = 0; break; }
    if (ok) m |= span(p, k);
  }
  return m;
}
#define ASC lrun_e(x, 1, 1)
#define DSC lrun_e(x, -1, -1)
#define INC lrun_e(x, 1, 9)
#define DEC lrun_e(x, -9, -1)
static int imax(int a, int b) { return a > b ? a : b; }
#define ST2 imax(lrun_e(x, 2, 2), lrun_e(x, -2, -2))
#define ST3 imax(lrun_e(x, 3, 3), lrun_e(x, -3, -3))

// e 패턴이 정확히 pat인 곳 (예: {1,1,-1,-1})
static int mpat_e(const X *x, const int *pat, int L) {
  int m = 0;
  for (int p = 0; p + L <= 8; p++) {
    int ok = 1; for (int i = 0; i < L; i++) if (x->e[p + i] != pat[i]) { ok = 0; break; }
    if (ok) m |= span(p, L + 1);
  }
  return m;
}
static const int P_HILL2[] = {1, 1, -1, -1}, P_HILL3[] = {1, 1, 1, -1, -1, -1};
static const int P_PIT2[] = {-1, -1, 1, 1}, P_PIT3[] = {-1, -1, -1, 1, 1, 1};

// ---------- 번갈아 / 깜빡 ----------
static int xbit(const X *x, int i) { return x->d[i] == x->d[i + 2] && x->d[i] != x->d[i + 1]; }
static int altlen(const X *x) {
  int best = 0, cur = 0;
  for (int i = 0; i < 7; i++) { if (xbit(x, i)) { cur++; if (cur > best) best = cur; } else cur = 0; }
  return best ? best + 2 : 0;
}
static int malt(const X *x, int k) {
  int m = 0;
  for (int p = 0; p + k <= 9; p++) {
    int ok = 1; for (int i = p; i <= p + k - 3; i++) if (!xbit(x, i)) { ok = 0; break; }
    if (ok) m |= span(p, k);
  }
  return m;
}
static int blink(const X *x) {  // 한 칸 건너 같은 숫자가 몇 번
  int best = 0;
  for (int p = 0; p < 7; p++) {
    int t = 1; for (int i = p; i < 7 && xbit(x, i); i += 2) t++;
    if (t > best) best = t;
  }
  return best;
}
static int mblink(const X *x, int t) {
  int m = 0;
  for (int p = 0; p + 2 * (t - 1) <= 8; p++) {
    int ok = 1; for (int j = 0; j < t - 1; j++) if (!xbit(x, p + 2 * j)) { ok = 0; break; }
    if (ok) for (int j = 0; j < t; j++) m |= 1 << (p + 2 * j);
  }
  return m;
}

// ---------- 대칭 ----------
static int ispal(const X *x, int p, int L) {
  int same = 1;
  for (int i = 0; i < L; i++) { if (x->d[p + i] != x->d[p + L - 1 - i]) return 0; if (x->d[p + i] != x->d[p]) same = 0; }
  return !same;
}
static int pallen(const X *x) {
  for (int L = 9; L >= 4; L--) for (int p = 0; p + L <= 9; p++) if (ispal(x, p, L)) return L;
  return 0;
}
static int mpal(const X *x, int L) {
  int m = 0; for (int p = 0; p + L <= 9; p++) if (ispal(x, p, L)) m |= span(p, L); return m;
}
static int rot(int a) { return a == 0 ? 0 : a == 1 ? 1 : a == 8 ? 8 : a == 6 ? 9 : a == 9 ? 6 : -1; }
static int isflip4(const X *x, int p) {
  if (rot(x->d[p]) != x->d[p + 3] || rot(x->d[p + 1]) != x->d[p + 2]) return 0;
  int a = x->d[p], b = x->d[p + 1];
  return a == 6 || a == 9 || b == 6 || b == 9;
}
static int mflip4(const X *x) { int m = 0; for (int p = 0; p <= 5; p++) if (isflip4(x, p)) m |= span(p, 4); return m; }
static int isbat(const X *x) {
  int k69 = 0;
  for (int i = 0; i < 4; i++) { if (rot(x->d[i]) != x->d[8 - i]) return 0; if (x->d[i] == 6 || x->d[i] == 9) k69 = 1; }
  if (!(x->d[4] == 0 || x->d[4] == 1 || x->d[4] == 8)) return 0;
  return k69;
}

// ---------- 짝꿍 구조 ----------
static int ischain(const X *x, int p, int k) {  // 서로 다른 짝꿍 k쌍이 붙어 있음
  for (int j = 0; j < k; j++) if (x->d[p + 2 * j] != x->d[p + 2 * j + 1]) return 0;
  for (int j = 0; j + 1 < k; j++) if (x->d[p + 2 * j + 1] == x->d[p + 2 * j + 2]) return 0;
  return 1;
}
static int chain(const X *x) {
  for (int k = 4; k >= 2; k--) for (int p = 0; p + 2 * k <= 9; p++) if (ischain(x, p, k)) return k;
  return 0;
}
static int mchain(const X *x, int k) { int m = 0; for (int p = 0; p + 2 * k <= 9; p++) if (ischain(x, p, k)) m |= span(p, 2 * k); return m; }
static int istrain(const X *x, int p, int k) {
  if (!ischain(x, p, k)) return 0;
  int s = x->d[p + 2] - x->d[p];
  if (s != 1 && s != -1) return 0;
  for (int j = 0; j + 1 < k; j++) if (x->d[p + 2 * j + 2] - x->d[p + 2 * j] != s) return 0;
  return 1;
}
static int train(const X *x) {
  for (int k = 4; k >= 3; k--) for (int p = 0; p + 2 * k <= 9; p++) if (istrain(x, p, k)) return k;
  return 0;
}
static int mtrain(const X *x, int k) { int m = 0; for (int p = 0; p + 2 * k <= 9; p++) if (istrain(x, p, k)) m |= span(p, 2 * k); return m; }
static int mlook(const X *x) {  // 똑같은 짝꿍이 서로 다른 덩어리로 2번
  int m = 0;
  for (int a = 0; a < x->nr; a++) for (int b = a + 1; b < x->nr; b++)
    if (x->rl[a] >= 2 && x->rl[b] >= 2 && x->rv[a] == x->rv[b]) m |= span(x->rs[a], x->rl[a]) | span(x->rs[b], x->rl[b]);
  return m;
}
static int msg2(const X *x) {  // 3개 덩어리 바로 옆에 2개 이상 덩어리
  int m = 0;
  for (int j = 0; j + 1 < x->nr; j++)
    if ((x->rl[j] >= 3 && x->rl[j + 1] >= 2) || (x->rl[j] >= 2 && x->rl[j + 1] >= 3)) m |= span(x->rs[j], x->rl[j] + x->rl[j + 1]);
  return m;
}
static int mrunsge(const X *x, int k) { int m = 0; for (int j = 0; j < x->nr; j++) if (x->rl[j] >= k) m |= span(x->rs[j], x->rl[j]); return m; }
static int mfish(const X *x) {  // AABBAA
  int m = 0;
  for (int j = 0; j + 2 < x->nr; j++) if (x->rl[j] >= 2 && x->rl[j + 1] == 2 && x->rl[j + 2] >= 2 && x->rv[j] == x->rv[j + 2]) m |= span(x->rs[j + 1] - 2, 6);
  return m;
}
static int mmaca(const X *x) {  // BAAAB
  int m = 0;
  for (int j = 0; j + 2 < x->nr; j++) if (x->rl[j + 1] == 3 && x->rv[j] == x->rv[j + 2]) m |= span(x->rs[j + 1] - 1, 5);
  return m;
}
static int mfat(const X *x) {  // AAABBAAA
  int m = 0;
  for (int j = 0; j + 2 < x->nr; j++) if (x->rl[j] >= 3 && x->rl[j + 1] == 2 && x->rl[j + 2] >= 3 && x->rv[j] == x->rv[j + 2]) m |= span(x->rs[j + 1] - 3, 8);
  return m;
}

// ---------- 개수 ----------
static int mcnt_ge(const X *x, int k) { int m = 0; for (int i = 0; i < 9; i++) if (x->c[x->d[i]] >= k) m |= 1 << i; return m; }
static int mcnt_eq(const X *x, int k) { int m = 0; for (int i = 0; i < 9; i++) if (x->c[x->d[i]] == k) m |= 1 << i; return m; }
static int mdig(const X *x, int v) { int m = 0; for (int i = 0; i < 9; i++) if (x->d[i] == v) m |= 1 << i; return m; }
static int ncnt_ge(const X *x, int k) { int n = 0; for (int v = 0; v < 10; v++) if (x->c[v] >= k) n++; return n; }
static int ncnt_eq(const X *x, int k) { int n = 0; for (int v = 0; v < 10; v++) if (x->c[v] == k) n++; return n; }
static int selfcnt(const X *x) { for (int v = 0; v < 10; v++) if (x->c[v] && x->c[v] != v) return 0; return 1; }
static int subset(const X *x, int setmask) { for (int v = 0; v < 10; v++) if (x->c[v] && !(setmask >> v & 1)) return 0; return 1; }
#define SET(m) subset(x, m)
static int oddrun(const X *x, int par) {
  int best = 0, cur = 0;
  for (int i = 0; i < 9; i++) { if ((x->d[i] & 1) == par) { cur++; if (cur > best) best = cur; } else cur = 0; }
  return best;
}
static int moddrun(const X *x, int par, int k) {
  int m = 0;
  for (int p = 0; p + k <= 9; p++) { int ok = 1; for (int i = p; i < p + k; i++) if ((x->d[i] & 1) != par) ok = 0; if (ok) m |= span(p, k); }
  return m;
}
static int paralt(const X *x) { for (int i = 0; i < 8; i++) if (((x->d[i] ^ x->d[i + 1]) & 1) == 0) return 0; return 1; }
static int nag(const X *x) {  // 같은 2자리(서로 다른 숫자)가 3번 이상 → 그 자리들
  int m = 0;
  for (int i = 0; i < 8; i++) {
    if (x->d[i] == x->d[i + 1]) continue;
    int n = 0, mm = 0;
    for (int j = 0; j < 8; j++) if (x->d[j] == x->d[i] && x->d[j + 1] == x->d[i + 1]) { n++; mm |= span(j, 2); }
    if (n >= 3) m |= mm;
  }
  return m;
}
static int blk3same(const X *x, int i) { return x->d[i] == x->d[i + 1] && x->d[i + 1] == x->d[i + 2]; }
static int eq3(const X *x, int i, int j) { return x->d[i] == x->d[j] && x->d[i + 1] == x->d[j + 1] && x->d[i + 2] == x->d[j + 2]; }
static int magain(const X *x) {  // 같은 3자리가 떨어져서 또
  int m = 0;
  for (int i = 0; i < 7; i++) for (int j = i + 4; j < 7; j++) if (eq3(x, i, j) && !blk3same(x, i)) m |= span(i, 3) | span(j, 3);
  return m;
}
static int mcopy(const X *x) { int m = 0; for (int i = 0; i <= 3; i++) if (eq3(x, i, i + 3) && !blk3same(x, i)) m |= span(i, 6); return m; }
static int isphone(const X *x, int i) {
  for (int k = 0; k < 4; k++) if (x->d[i + k] != x->d[i + 4 + k]) return 0;
  return !(x->d[i] == x->d[i + 1] && x->d[i] == x->d[i + 2] && x->d[i] == x->d[i + 3]);
}
static int mphone(const X *x) { int m = 0; for (int i = 0; i <= 1; i++) if (isphone(x, i)) m |= span(i, 8); return m; }
static int isspam(const X *x) { return eq3(x, 0, 3) && eq3(x, 3, 6) && !blk3same(x, 0); }
static int iszag(const X *x) {
  return x->d[3] == x->d[2] && x->d[4] == x->d[1] && x->d[5] == x->d[0] && eq3(x, 0, 6) && !blk3same(x, 0);
}

// ---------- 오르내림 전체 모양 ----------
static int zig(const X *x) {
  for (int i = 0; i < 8; i++) if (x->e[i] == 0) return 0;
  for (int i = 0; i < 7; i++) if ((x->e[i] > 0) == (x->e[i + 1] > 0)) return 0;
  return 1;
}
static int alle(const X *x, int lo, int hi, int a, int b) { for (int i = a; i <= b; i++) if (x->e[i] < lo || x->e[i] > hi) return 0; return 1; }
#define ALLE(lo, hi, a, b) alle(x, lo, hi, a, b)
static int absall(const X *x, int lo, int hi) { for (int i = 0; i < 8; i++) { int a = abs(x->e[i]); if (a < lo || a > hi) return 0; } return 1; }
static int umax(const X *x, int p) { for (int i = 0; i < 9; i++) if (i != p && x->d[i] >= x->d[p]) return 0; return 1; }
static int umin(const X *x, int p) { for (int i = 0; i < 9; i++) if (i != p && x->d[i] <= x->d[p]) return 0; return 1; }

// ---------- 자리 ----------
static int lead(const X *x, int v) { int k = 0; while (k < 9 && x->d[k] == v) k++; return k; }
static int tail(const X *x, int v) { int k = 0; while (k < 9 && x->d[8 - k] == v) k++; return k; }
static int place(const X *x) { int n = 0; for (int i = 0; i < 9; i++) if (x->d[i] == i + 1) n++; return n; }
static int mplace(const X *x) { int m = 0; for (int i = 0; i < 9; i++) if (x->d[i] == i + 1) m |= 1 << i; return m; }
static int tilt(const X *x) {
  int a = 1, b = 1;
  for (int i = 0; i < 4; i++) { if (x->d[i] > 4 || x->d[5 + i] < 5) a = 0; if (x->d[i] < 5 || x->d[5 + i] > 4) b = 0; }
  return a || b;
}

// ---------- 산수 ----------
static int mmul(const X *x) { int m = 0; for (int i = 0; i <= 5; i++) { int p = x->d[i] * x->d[i + 1]; if (p >= 10 && x->d[i + 2] * 10 + x->d[i + 3] == p) m |= span(i, 4); } return m; }
static int msq(const X *x) { int m = 0; for (int i = 0; i <= 6; i++) { int p = x->d[i] * x->d[i]; if (p >= 10 && x->d[i + 1] * 10 + x->d[i + 2] == p) m |= span(i, 3); } return m; }
static int madd(const X *x) { int m = 0; for (int i = 0; i <= 5; i++) { int p = x->d[i] + x->d[i + 1]; if (p >= 10 && x->d[i + 2] * 10 + x->d[i + 3] == p) m |= span(i, 4); } return m; }
static int isfib(const X *x, int p, int k) {
  if (x->d[p] == 0 && x->d[p + 1] == 0) return 0;
  for (int j = p; j + 2 < p + k; j++) if (x->d[j + 2] != x->d[j] + x->d[j + 1]) return 0;
  return 1;
}
static int fib(const X *x) { for (int k = 9; k >= 4; k--) for (int p = 0; p + k <= 9; p++) if (isfib(x, p, k)) return k; return 0; }
static int mfib(const X *x, int k) { int m = 0; for (int p = 0; p + k <= 9; p++) if (isfib(x, p, k)) m |= span(p, k); return m; }
static int blk(const X *x, int i) { return x->d[i] * 100 + x->d[i + 1] * 10 + x->d[i + 2]; }
#define BA blk(x, 0)
#define BB blk(x, 3)
#define BC blk(x, 6)

// ---------- 키패드 ----------
static const int BIDX[10] = {-1, 0, 1, 2, 7, -1, 3, 6, 5, 4};  // 테두리 1,2,3,6,9,8,7,4
static int isborder(const X *x, int p, int k) {
  for (int i = p; i < p + k; i++) if (BIDX[x->d[i]] < 0) return 0;
  int s = (BIDX[x->d[p + 1]] - BIDX[x->d[p]] + 8) % 8;
  if (s != 1 && s != 7) return 0;
  for (int i = p; i + 1 < p + k; i++) if ((BIDX[x->d[i + 1]] - BIDX[x->d[i]] + 8) % 8 != s) return 0;
  return 1;
}
static int border(const X *x) { for (int k = 9; k >= 6; k--) for (int p = 0; p + k <= 9; p++) if (isborder(x, p, k)) return k; return 0; }
static int mborder(const X *x, int k) { int m = 0; for (int p = 0; p + k <= 9; p++) if (isborder(x, p, k)) m |= span(p, k); return m; }
static int padadj(int a, int b) {
  static const int R[10] = {3, 0, 0, 0, 1, 1, 1, 2, 2, 2}, Cc[10] = {1, 0, 1, 2, 0, 1, 2, 0, 1, 2};
  return abs(R[a] - R[b]) + abs(Cc[a] - Cc[b]) == 1;
}
static int walk(const X *x) { for (int i = 0; i < 8; i++) if (!padadj(x->d[i], x->d[i + 1])) return 0; return 1; }

// 지역번호가 나온 횟수
static const char *REGION[] = {"031", "032", "033", "041", "042", "043", "044", "051", "052", "053", "054", "055", "061", "062", "063", "064", 0};
static int nregion(const X *x) { int n = 0; for (int i = 0; REGION[i]; i++) n += occ(x, REGION[i]); return n; }
static int mregion(const X *x) { int m = 0; for (int i = 0; REGION[i]; i++) m |= mall(x, REGION[i]); return m; }

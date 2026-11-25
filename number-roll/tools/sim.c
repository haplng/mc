// 경제 시뮬레이터: 한 사람이 처음부터 플레이할 때 언제 무엇을 사게 되는지 본다.
//   sim HOURS ACTIVE SEED [quiet]       ACTIVE: 자동 굴리기를 산 뒤에도 직접 굴리는 비율 (0..1)
//   sim jstat N [행운단계]               조커·강화별 평균 효과
// 사는 규칙: 살 수 있는 것 중 제일 싼 것부터. 조커는 실제로 준 효과가 큰 것부터 낀다.
// 환경 변수 NOADV NOJOK NOPERK NOMIS 를 주면 그 요소를 끈다. TABLE 을 주면 끝에 달성 시각 표를 찍는다.
// 필요한 것: ref.h, ref_hands.h, sim_data.h (tools/simgen.py 가 만든다)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ref.h"
#include "ref_hands.h"
#include "sim_data.h"

static unsigned long long RS = 88172645463325252ULL;
static inline unsigned long long rnd(void) { RS ^= RS << 13; RS ^= RS >> 7; RS ^= RS << 17; return RS; }
static inline int rnum(void) { return (int)(rnd() % 1000000000ULL); }

typedef struct {
  double coins; int u1, u2, u3, u4, unl, e1, e2, e4, e5, ept;
  int jo[NJOK];           // 0 없음 1 있음 2 끼는 중
  int jslot, jeq, jown;
  int cnt[NHAND];
  double st[NSTAT];
  int ft[6], adv[NADV];
  int misd[3][5], misL[3]; double misc[3];
  double jnum[NJOK], jden, misr, vr;     // 조커 효과 추정용
  int zc, hn, zl;
  double earned;
} Pl;
static Pl P;
static double TICKS = 0, INCM = 0;     // INCM: 최근 분당 수입 (부드럽게)
static int QUIET = 0, NOADV = 0, NOJOK = 0, NOPERK = 0, NOMIS = 0;
static double ACTIVE = 1.0;
static double WRC = 0, WRR = 0, wEarn = 0, wRolls = 0, wT = 0;   // 최근 1분 동안 굴려서 번 코인 / 굴린 숫자
static double advT[NADV], advI[NADV], unlT[NUNL], unlI[NUNL], jokT[NJOK], jokI[NJOK];

static const char *won(double c) {
  static char b[8][40]; static int k; char *s = b[k++ & 7];
  if (c < 1e4) snprintf(s, 40, "%.0f", c); else if (c < 1e8) snprintf(s, 40, "%.4g만", c / 1e4); else if (c < 1e12) snprintf(s, 40, "%.4g억", c / 1e8); else snprintf(s, 40, "%.4g조", c / 1e12);
  return s;
}
static void say(const char *what) {
  if (QUIET) return;
  double m = TICKS / 1200.0;
  printf("%7.1f분 (%5.2f시간)  %-30s 코인 %10s  분당 %9s  굴림 %8.0f  도감 %3.0f  ★%4.0f ⭐%d\n", m, m / 60, what, won(P.coins), won(INCM), P.st[S_rolls], P.st[S_found], P.st[S_stot], P.ept);
}
static void addc(double c) { P.coins += c; if (P.coins > 9.999e15) P.coins = 9.999e15; }
static int star_of(int c, int t) { return c >= STAR_T[t][3] ? 4 : c >= STAR_T[t][2] ? 3 : c >= STAR_T[t][1] ? 2 : c >= STAR_T[t][0] ? 1 : 0; }

// ---- 숫자 하나 ----
static X gx; static unsigned char ghit[NHAND]; static int g_n, g_nh, g_bt;
static void eval(int n) {
  g_n = n; prep(&gx, n); detect(&gx, ghit, P.unl >= ST_t4, P.unl >= ST_t5);
  g_nh = 0; g_bt = -1;
  for (int i = 0; i < NHAND; i++) if (ghit[i] && REAL[i]) { g_nh++; if (TIER[i] > g_bt) g_bt = TIER[i]; }
}
static void luck1(void) {
  for (int lt = 0; lt < 60; lt++) {
    if (P.e5 == 1 && g_bt >= 0) return;
    if (P.e5 >= 2 && g_bt >= 1) return;
    if (g_bt < 0) P.st[S_zn]++;
    eval(rnum());
  }
}
static double g_p[4], g_pf[5], g_pay;
static int g_man, g_cdig, g_ntier;
// 부분 조커: 기본 코인이 얼마로 바뀌나 (p: 등급별 코인, px: 덤)
static void part_apply(int j, double *p, double *px) {
  int a = JOK[j].a, m = JOK[j].b;
  switch (a) {
    case PT_p0: p[0] *= m; break;
    case PT_p12: p[1] *= m; p[2] *= m; break;
    case PT_p3: p[3] *= m; break;
    case PT_same: *px += (m - 1) * g_pf[1]; break;
    case PT_stair: *px += (m - 1) * g_pf[2]; break;
    case PT_mirror: *px += (m - 1) * g_pf[3]; break;
    case PT_word: *px += (m - 1) * g_pf[4]; break;
  }
}
// 전체 조커: 이 숫자의 코인이 몇 % 가 되나 (100 = 그대로)
static double whole_pct(int j) {
  int a = JOK[j].a, b = JOK[j].b;
  switch (JOK[j].kind) {
    case K_digit: return 100 + gx.c[a] * b;
    case K_nh_le: return g_nh <= a ? b : 100;
    case K_nh_ge: return g_nh >= a ? b : 100;
    case K_tiers: return g_ntier >= a ? b : 100;
    case K_manual: return g_man ? a : 100;
    case K_auto: return g_man ? 100 : a;
    case K_found: return 100 + (int)(P.st[S_found] / a) * b;
    case K_stars: return 100 + (int)(P.st[S_stot] / a) * b;
    case K_cdig: return 100 + g_cdig * a;
  }
  return 100;
}
static double value_of(const double *p, double px) {
  double pay = p[0] + p[1] + p[2] + p[3] + px;
  double v = pay + (p[2] + p[3]) * P.e1 * 0.5;
  if (g_nh >= 2) v += pay * (g_nh - 1) * P.e2 * 0.1;
  return v;
}
static void new_mission(int i) {
  P.misL[i] = 0;
  if (P.unl < MISST[i] || NOMIS) return;
  P.misL[i] = MISL[i];
  int v = (int)(rnd() % (i == 0 ? 1000 : i == 1 ? 10000 : 100000));
  for (int j = MISL[i] - 1; j >= 0; j--) { P.misd[i][j] = v % 10; v /= 10; }
  P.misc[i] = MISB[i] * (1 + P.u4 / 2.0);
  if (WRR > 0 && MISK[i] * WRC / WRR > P.misc[i]) P.misc[i] = (double)(long)(MISK[i] * WRC / WRR);
}
static int mission_joker(void) { for (int j = 0; j < NJOK; j++) if (JOK[j].kind == K_mission && P.jo[j] == 2) return JOK[j].a; return 1; }
static double roll_one(int man) {
  g_man = man;
  eval(rnum());
  if (P.e5 >= 1) {
    luck1();
    if (P.e5 >= 3 && g_bt == 1) {
      int lkn = g_n, lkb = g_bt, lkh = g_nh;
      eval(rnum()); luck1();
      if (g_bt < lkb || (g_bt == lkb && g_nh < lkh)) eval(lkn);
    }
  }
  g_p[0] = g_p[1] = g_p[2] = g_p[3] = 0; memset(g_pf, 0, sizeof g_pf); int tiers[6] = {0};
  for (int i = 0; i < NHAND; i++) if (ghit[i] && REAL[i]) {
    int t = TIER[i];
    int c = ++P.cnt[i];
    int s = star_of(c, t);
    double hp = (double)(long)(PAYB[i] * (4 + s) / 4.0 + 0.5);
    g_p[t < 3 ? t : 3] += hp; g_pf[FAMJ[i]] += hp; tiers[t] = 1;
    if (c == 1) { P.st[S_found]++; P.ft[t]++; P.st[S_stot]++; }
    for (int k = 0; k < 4; k++) if (c == STAR_T[t][k]) { P.ept++; P.st[S_stot]++; if (k + 2 > P.st[S_smax]) P.st[S_smax] = k + 2; if (k == 3) P.st[S_s5n]++; }
  }
  g_ntier = 0; for (int t = 0; t < 6; t++) g_ntier += tiers[t];
  g_pay = g_p[0] + g_p[1] + g_p[2] + g_p[3];
  // 미션
  double mis = 0;
  for (int i = 0; i < 3; i++) if (P.misL[i]) {
    int L = P.misL[i], ok = 0;
    for (int p = 0; p + L <= 9 && !ok; p++) { int j = 0; while (j < L && gx.d[p + j] == P.misd[i][j]) j++; if (j == L) ok = 1; }
    if (ok) {
      double rw = MISB[i] * (1 + P.u4 / 2.0);     // 보상은 깰 때 수입으로 다시 셈
      if (WRR > 0 && MISK[i] * WRC / WRR > rw) rw = (double)(long)(MISK[i] * WRC / WRR);
      mis += rw; P.st[S_mdone]++; new_mission(i);
    }
  }
  if (mis > 0) { double cg = mis * mission_joker(); addc(cg); P.earned += cg; }
  P.misr = P.misr * 0.9995 + mis * 0.0005;
  // 코인
  double base = value_of(g_p, 0);
  double p[4] = {g_p[0], g_p[1], g_p[2], g_p[3]}, px = 0;
  for (int j = 0; j < NJOK; j++) if (P.jo[j] == 2 && JOK[j].kind == K_part) part_apply(j, p, &px);
  double v = value_of(p, px);
  for (int j = 0; j < NJOK; j++) if (P.jo[j] == 2 && JOK[j].kind != K_part && JOK[j].kind != K_mission) v = v * whole_pct(j) / 100.0;
  double boost = 1 + P.u4 / 2.0;
  // 조커별 효과 추정 (가진 것 전부)
  P.jden = P.jden * 0.9995 + base * 0.0005;
  for (int j = 0; j < NJOK; j++) if (P.jo[j]) {
    double f = 1;
    if (JOK[j].kind == K_part) { double q[4] = {g_p[0], g_p[1], g_p[2], g_p[3]}, qx = 0; part_apply(j, q, &qx); f = base > 0 ? value_of(q, qx) / base : 1; }
    else if (JOK[j].kind != K_mission) f = whole_pct(j) / 100.0;
    P.jnum[j] = P.jnum[j] * 0.9995 + base * (f - 1) * 0.0005;
  }
  v *= boost;
  if (v > 2e12) v = 2e12;
  v = (double)(long)v;
  P.vr = P.vr * 0.9995 + v * 0.0005;
  if (v > P.st[S_mxr]) P.st[S_mxr] = v;
  if (g_nh > P.st[S_mxn]) P.st[S_mxn] = g_nh;
  if (g_bt > P.st[S_mxt]) P.st[S_mxt] = g_bt;
  P.hn++;
  if (g_nh == 0) P.st[S_zn]++;
  return v;
}

// ---- 도전과제 ----
static void advs(void) {
  P.st[S_coins] = P.coins; P.st[S_cq] = P.coins > 1e9 ? 1e9 : P.coins; P.st[S_cb] = (double)(long)(P.coins / 1e9); P.st[S_u1] = P.u1; P.st[S_u2] = P.u2; P.st[S_u3] = P.u3; P.st[S_u4] = P.u4; P.st[S_unl] = P.unl;
  P.st[S_e5] = P.e5; P.st[S_jown] = P.jown; P.st[S_jeq] = P.jeq;
  for (int a = 0; a < NADV; a++) if (!P.adv[a]) {
    const Adv *A = &ADVS[a]; int ok = 0;
    switch (A->kind) {
      case 0: ok = 1; break;
      case 1: ok = P.st[A->a] >= A->b; break;
      case 2: ok = P.cnt[A->a] >= 1; break;
      case 3: ok = P.ft[A->a] >= A->b; break;
      case 4: { ok = 1; for (const int *c = COLS[A->a]; *c >= 0; c++) if (!P.cnt[*c]) { ok = 0; break; } break; }
      case 5:
        if (!strcmp(A->key, "broke")) ok = P.coins <= 9 && P.st[S_ubuy] >= 1;
        else if (!strcmp(A->key, "uall")) ok = P.u1 >= 10 && P.u2 >= 10 && P.u3 >= 7 && P.u4 >= 10;
        else if (!strcmp(A->key, "perk_all")) ok = P.e1 >= N_PERK_e1 && P.e2 >= N_PERK_e2 && P.e4 >= N_PERK_e4 && P.e5 >= N_PERK_e5;
        break;
    }
    if (ok) { P.adv[a] = 1; advT[a] = TICKS / 1200.0; advI[a] = INCM; if (!NOADV) addc(A->reward); }
  }
}

// ---- 사기 ----
static double jfactor(int j) {
  if (JOK[j].kind == K_mission) return P.vr > 0 ? 1 + (JOK[j].a - 1) * P.misr / (P.vr + P.misr) : 1;   // 미션 수입이 전체에서 차지하는 몫
  return P.jden > 0 ? 1 + P.jnum[j] / P.jden : 1;
}
static void equip(void) {
  for (int j = 0; j < NJOK; j++) if (P.jo[j] == 2) P.jo[j] = 1;
  P.jeq = 0;
  for (int k = 0; k < P.jslot; k++) {
    int best = -1; double bf = 0;
    for (int j = 0; j < NJOK; j++) if (P.jo[j] == 1) { double f = jfactor(j); if (best < 0 || f > bf) { best = j; bf = f; } }
    if (best < 0) break;
    P.jo[best] = 2; P.jeq++;
  }
}
static int buy_one(void) {
  double best = -1; int what = -1, arg = 0;
#define CAND(price, w, a) do { double pr = (price); if (pr <= P.coins && (best < 0 || pr < best)) { best = pr; what = (w); arg = (a); } } while (0)
  if (P.u1 < N_COST_U1) CAND(COST_U1[P.u1], 1, 0);
  if (P.u2 < N_COST_U2) CAND(COST_U2[P.u2], 2, 0);
  if (P.u3 < N_COST_U3) CAND(COST_U3[P.u3], 3, 0);
  if (P.u4 < N_COST_U4) CAND(COST_U4[P.u4], 4, 0);
  if (P.unl < NUNL) CAND(UNLP[P.unl], 5, 0);
  if (P.jslot >= 1 && !NOJOK) for (int j = 0; j < NJOK; j++) if (!P.jo[j]) CAND(JOKP[j], 6, j);
  if (what < 0) return 0;
  P.coins -= best; char buf[128];
  switch (what) {
    case 1: P.u1++; P.st[S_ubuy]++; if (P.u1 == N_COST_U1) say("⚡ 속도 최대"); break;
    case 2: P.u2++; P.st[S_ubuy]++; if (P.u2 == 1) say("⟳ 자동 굴리기 삼"); if (P.u2 == N_COST_U2) say("⟳ 자동 최대"); break;
    case 3: P.u3++; P.st[S_ubuy]++; if (P.u3 == N_COST_U3) say("✚ 여러 개 최대"); break;
    case 4: P.u4++; P.st[S_ubuy]++; if (P.u4 == N_COST_U4) say("⛃ 부스트 최대"); break;
    case 5:
      unlT[P.unl] = TICKS / 1200.0; unlI[P.unl] = INCM;
      P.unl++; snprintf(buf, sizeof buf, "🔓 해금 %s (%s)", UNLN[P.unl - 1], won(best)); say(buf);
      for (int i = 0; i < 3; i++) if (P.unl == MISST[i]) new_mission(i);
      if (P.unl == ST_jk1) P.jslot = 1;
      if (P.unl == ST_jk2) P.jslot = 2;
      if (P.unl == ST_jk3) P.jslot = 3;
      if (P.unl == ST_jk4) P.jslot = 4;
      equip(); break;
    case 6: jokT[arg] = TICKS / 1200.0; jokI[arg] = INCM; P.jo[arg] = 1; P.jown++; snprintf(buf, sizeof buf, "🃏 조커 %s (%s)", JOKN[arg], won(best)); say(buf); equip(); break;
  }
  return 1;
}
static void perks(void) {
  if (NOPERK) return;
  for (;;) {
    int best = -1, w = 0;
#define PC(lv, arr, n, id) if ((lv) < (n) && arr[lv] <= P.ept && (best < 0 || arr[lv] < best)) { best = arr[lv]; w = id; }
    PC(P.e1, PERKC_e1, N_PERK_e1, 1) PC(P.e2, PERKC_e2, N_PERK_e2, 2) PC(P.e4, PERKC_e4, N_PERK_e4, 4) PC(P.e5, PERKC_e5, N_PERK_e5, 5)
    if (best < 0) return;
    P.ept -= best; P.st[S_pbuy]++;
    char buf[64];
    if (w == 1) { P.e1++; snprintf(buf, sizeof buf, "⭐ 💎 고급 족보 %d", P.e1); }
    if (w == 2) { P.e2++; snprintf(buf, sizeof buf, "⭐ 🎰 콤보 %d", P.e2); }
    if (w == 4) { P.e4++; snprintf(buf, sizeof buf, "⭐ ⏩ 빨리 보기 %d", P.e4); }
    if (w == 5) { P.e5++; snprintf(buf, sizeof buf, "⭐ 🍀 행운 %d", P.e5); }
    say(buf);
  }
}

// 조커·강화별 평균 효과
static int jstat(long N, int luck) {
  memset(&P, 0, sizeof P); P.unl = NUNL; P.e5 = luck; P.st[S_found] = 300; P.st[S_stot] = 800; g_cdig = 10;
  double pay = 0, pt[4] = {0}, pf[5] = {0}, jb[NJOK] = {0}, nhs = 0, e1 = 0, e2 = 0; long nhh[40] = {0}, btc[7] = {0};
  for (long k = 0; k < N; k++) {
    roll_one(1);
    pay += g_pay; for (int t = 0; t < 4; t++) pt[t] += g_p[t];
    for (int f = 0; f < 5; f++) pf[f] += g_pf[f];
    nhs += g_nh; nhh[g_nh < 39 ? g_nh : 39]++; btc[g_bt + 1]++;
    e1 += (g_p[2] + g_p[3]) * 0.5; if (g_nh >= 2) e2 += g_pay * (g_nh - 1) * 0.1;
    for (int j = 0; j < NJOK; j++) {
      double f = 1; g_man = JOK[j].kind != K_auto;
      if (JOK[j].kind == K_part) { double q[4] = {g_p[0], g_p[1], g_p[2], g_p[3]}, qx = 0; part_apply(j, q, &qx); f = g_pay > 0 ? (q[0] + q[1] + q[2] + q[3] + qx) / g_pay : 1; }
      else if (JOK[j].kind != K_mission) f = whole_pct(j) / 100.0;
      jb[j] += g_pay * (f - 1);
    }
    memset(P.cnt, 0, sizeof P.cnt); P.st[S_found] = 300; P.st[S_stot] = 800;
  }
  printf("행운 %d: 숫자당 평균 %.0f⛃ (흔함 %.0f 보통 %.0f 희귀 %.0f 영웅+ %.0f), 족보 %.2f개\n", luck, pay / N, pt[0] / N, pt[1] / N, pt[2] / N, pt[3] / N, nhs / N);
  printf("  계열: 그밖 %.0f 같은숫자 %.0f 오르내림 %.0f 대칭 %.0f 말장난·합체 %.0f\n", pf[0] / N, pf[1] / N, pf[2] / N, pf[3] / N, pf[4] / N);
  printf("  최고 등급: 꽝 %.2f%% 흔함 %.1f%% 보통 %.1f%% 희귀 %.1f%% 영웅 %.2f%% 전설 %.3f%% 신화 %.4f%%\n", 100.0 * btc[0] / N, 100.0 * btc[1] / N, 100.0 * btc[2] / N, 100.0 * btc[3] / N, 100.0 * btc[4] / N, 100.0 * btc[5] / N, 100.0 * btc[6] / N);
  printf("  💎 한 단계 +%.1f%%   🎰 한 단계 +%.1f%%\n", 100 * e1 / pay, 100 * e2 / pay);
  for (int j = 0; j < NJOK; j++) printf("  %2d %-24s ×%.2f\n", j + 1, JOKN[j], 1 + jb[j] / pay);
  printf("  족보 수:"); for (int i = 0; i < 16; i++) printf(" %d:%.1f%%", i, 100.0 * nhh[i] / N);
  printf("\n");
  return 0;
}

int main(int argc, char **argv) {
  if (argc > 1 && !strcmp(argv[1], "jstat")) return jstat(atol(argv[2]), argc > 3 ? atoi(argv[3]) : 0);
  double hours = argc > 1 ? atof(argv[1]) : 10; ACTIVE = argc > 2 ? atof(argv[2]) : 1.0;
  if (argc > 3) RS ^= (unsigned long long)atol(argv[3]) * 0x9E3779B97F4A7C15ULL;
  QUIET = argc > 4 && atoi(argv[4]);
  NOADV = getenv("NOADV") != 0; NOJOK = getenv("NOJOK") != 0; NOPERK = getenv("NOPERK") != 0; NOMIS = getenv("NOMIS") != 0;
  for (int i = 0; i < 20; i++) rnd();
  memset(&P, 0, sizeof P); P.st[S_mxt] = -1;
  for (int a = 0; a < NADV; a++) advT[a] = -1;
  for (int a = 0; a < NUNL; a++) unlT[a] = -1;
  for (int a = 0; a < NJOK; a++) jokT[a] = -1;
  double tman = 0, tauto = 1e18, end = hours * 72000.0, nextrep = 1200 * 5; int eqt = 0;
  double lastearn = 0, lastt = 0, lastfound = -1, incE = 0, incT = 0;
  advs();
  while (TICKS < end) {
    int man = tman <= tauto;
    TICKS = man ? tman : tauto;
    g_cdig = 1; for (double c = P.coins; c >= 10; c /= 10) g_cdig++;
    int n = P.u3 + 1; double sum = 0, bestrt = -1; int bestnh = 0;
    if (man && P.u2 >= 1 && (rnd() % 1000) >= (unsigned long long)(ACTIVE * 1000)) {
      tman = TICKS + SPEED_T[P.u1] + 40;           // 이번엔 손을 쉼
    } else {
      for (int k = 0; k < n; k++) {
        double rt = roll_one(man); sum += rt; P.st[S_rolls]++; if (!man) P.st[S_arl]++;
        if (rt > bestrt) { bestrt = rt; bestnh = g_nh; }
      }
      addc(sum); P.earned += sum; wEarn += sum; wRolls += n;
      if (man) tman = TICKS + SPEED_T[P.u1] + (P.e4 >= 5 ? 0 : bestnh * (10 - 2 * P.e4)) + 2;
      else { int per = SPEED_T[P.u1] + AUTO_END[P.u2] - 1, steps = (n + 3) / 4; tauto = TICKS + (per > steps ? per : steps); }
    }
    if (TICKS - wT >= 1200) { WRC = wEarn; WRR = wRolls; wEarn = wRolls = 0; wT = TICKS; }
    // 최근 수입 (몇 분의 평균)
    if (TICKS - incT >= 600) { double r = (P.earned - incE) / ((TICKS - incT) / 1200.0); INCM = INCM * 0.7 + r * 0.3; incE = P.earned; incT = TICKS; }
    advs();
    while (buy_one()) advs();
    if (P.u2 >= 1 && tauto > 1e17) tauto = TICKS + 1;
    perks();
    if (++eqt >= 400) { eqt = 0; equip(); }
    if ((long)P.st[S_found] / 50 != (long)lastfound / 50 && P.st[S_found] >= 50) { char buf[64]; snprintf(buf, sizeof buf, "📖 도감 %ld개", (long)P.st[S_found] / 50 * 50); say(buf); }
    lastfound = P.st[S_found];
    if (TICKS >= nextrep) {
      if (!QUIET) {
        double m = TICKS / 1200.0;
        printf("  ── %6.0f분: 분당 %s⛃, 속도%d 자동%d 여러%d 부스트%d, 💎%d 🎰%d ⏩%d 🍀%d, 도감 %d/%d/%d/%d/%d/%d, 미션 %.0f, 조커:", m, won((P.earned - lastearn) / ((TICKS - lastt) / 1200.0)),
               P.u1, P.u2, P.u3, P.u4, P.e1, P.e2, P.e4, P.e5, P.ft[0], P.ft[1], P.ft[2], P.ft[3], P.ft[4], P.ft[5], P.st[S_mdone]);
        for (int j = 0; j < NJOK; j++) if (P.jo[j] == 2) printf(" %s(×%.2f)", JOKN[j], jfactor(j));
        printf("\n");
      }
      lastearn = P.earned; lastt = TICKS; nextrep = TICKS < 72000 ? TICKS + 6000 : TICKS < 720000 ? TICKS + 36000 : TICKS + 216000;
    }
  }
  int na = 0; for (int a = 0; a < NADV; a++) na += P.adv[a];
  printf("끝 %.1f시간: 코인 %s, 굴림 %.0f, 도감 %.0f (%d/%d/%d/%d/%d/%d), ★%.0f ⭐남음 %d, 도전과제 %d/%d, 해금 %d, 조커 %d, 번 코인 %s\n", hours, won(P.coins), P.st[S_rolls], P.st[S_found],
         P.ft[0], P.ft[1], P.ft[2], P.ft[3], P.ft[4], P.ft[5], P.st[S_stot], P.ept, na, NADV, P.unl, P.jown, won(P.earned));
  if (getenv("TABLE")) {
    printf("\n[도전과제] 열쇠, 달성(분), 그때 분당 수입, 지금 보상, 보상/수입(분)\n");
    for (int a = 0; a < NADV; a++) printf("  %-10s %8.1f %10s %10s %6.2f\n", ADVS[a].key, advT[a], advT[a] < 0 ? "-" : won(advI[a]), won(ADVS[a].reward), advT[a] < 0 || advI[a] <= 0 ? 0 : ADVS[a].reward / advI[a]);
    printf("[해금]\n");
    for (int a = 0; a < NUNL; a++) printf("  %-6s %8.1f분 값 %10s 그때 분당 %10s\n", UNLN[a], unlT[a], won(UNLP[a]), won(unlI[a]));
    printf("[조커]\n");
    for (int a = 0; a < NJOK; a++) printf("  %-22s %8.1f분 값 %10s 그때 분당 %10s  효과 ×%.2f\n", JOKN[a], jokT[a], won(JOKP[a]), won(jokI[a]), jfactor(a));
  }
  return 0;
}

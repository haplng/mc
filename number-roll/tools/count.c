// 족보별 걸리는 횟수를 센다:  count LO HI STEP [예시파일]  → JSON 한 줄
// 예시파일을 주면 족보마다 최대 RES개의 숫자를 고르게 뽑아 적는다 (자리 표시 검증용).
#include <stdio.h>
#include "ref.h"
#include "ref_hands.h"
#define RES 48
int main(int argc, char **argv) {
  long lo = atol(argv[1]), hi = atol(argv[2]), step = atol(argv[3]);
  static long cnt[NHAND]; static int ex[NHAND][RES]; static long nhh[64];
  unsigned char hit[NHAND]; X x; long tot = 0; unsigned long long rs = 88172645463325252ULL;
  for (long n = lo; n < hi; n += step) {
    prep(&x, (int)n); detect(&x, hit, 1, 1); tot++;
    int nh = 0;
    for (int i = 0; i < NHAND; i++) if (hit[i]) {
      nh++;
      if (cnt[i] < RES) ex[i][cnt[i]] = (int)n;
      else { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; unsigned long long r = rs % (unsigned long long)(cnt[i] + 1); if (r < RES) ex[i][r] = (int)n; }
      cnt[i]++;
    }
    nhh[nh < 63 ? nh : 63]++;
  }
  printf("{\"total\": %ld, \"cnt\": {", tot);
  for (int i = 0; i < NHAND; i++) printf("%s\"%s\": [%ld, %d, %d, %d]", i ? ", " : "", KEY[i], cnt[i], ex[i][0], ex[i][1], ex[i][2]);
  printf("}, \"nh\": [");
  for (int i = 0; i < 64; i++) printf("%s%ld", i ? ", " : "", nhh[i]);
  printf("]}\n");
  if (argc > 4) {
    FILE *f = fopen(argv[4], "w");
    for (int i = 0; i < NHAND; i++) for (int j = 0; j < RES && j < cnt[i]; j++) fprintf(f, "%d\n", ex[i][j]);
    fclose(f);
  }
  return 0;
}

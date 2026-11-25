// 숫자에 걸리는 족보를 기준 구현으로 알려 준다:  which 477155509 [ul4 ul5]
#include <stdio.h>
#include "ref.h"
#include "ref_hands.h"
int main(int argc, char **argv) {
  X x; unsigned char hit[NHAND];
  int ul4 = argc > 2 ? atoi(argv[2]) : 1, ul5 = argc > 3 ? atoi(argv[3]) : 1;
  prep(&x, atoi(argv[1])); detect(&x, hit, ul4, ul5);
  for (int i = 0; i < NHAND; i++) if (hit[i]) { int m = marks(&x, i); printf("%s ", KEY[i]); for (int b = 0; b < 9; b++) putchar((m >> b & 1) ? '0' + x.d[b] : '.'); printf("\n"); }
  return 0;
}

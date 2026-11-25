# 숫자 굴리기

마인크래프트 자바 26.3용 데이터팩 맵. 9자리 숫자를 굴려서 그 안에 숨은 **족보**를 찾으면 코인을 받는 방치형 게임.

## 플레이

`dice_roll.zip`을 월드의 `datapacks` 폴더에 넣으면 돼 (방은 데이터팩이 알아서 지음).

- 빨간 블록(나중엔 주사위)을 우클릭하면 숫자 9자리가 하나씩 나오고, 걸린 족보만큼 코인을 받아.
- **족보 400개** — 흔함 41 / 보통 89 / 희귀 100 / 영웅 61 / 전설 50 / 신화 59. 목록은 [HANDS.md](HANDS.md).
  코인은 `2 ÷ 확률`, 같은 족보를 많이 뽑으면 별(★)이 올라 25%씩 더 받아.
- **⛃ 코인 상점** — 속도 · 자동 굴리기 · 여러 개 · 부스트, 그리고 **🔓 해금** 10단계
  (미션 3종 · 주사위 · 조커 칸 4개 · 전설 · 신화).
- **⭐ 강화** — 별이 하나 오를 때마다 ⭐ +1. 💎 고급 족보 · 🎰 콤보 · ⏩ 빨리 보기 · 🍀 행운.
- **🃏 조커 18장** — 끼고 있으면 조건이 맞는 숫자에서 코인을 더 받아. 여러 장이면 서로 곱해져.
- **📋 미션** — 정해진 숫자열이 들어간 숫자를 뽑으면 보상 (숫자 하나 평균 수입의 30 / 300 / 3,000배).
- **🏆 도전과제 100개**, **📖 도감**, 기록 · 검색, 통계.
- 코인은 9,999조까지. 레벨은 없어.

대략 이런 속도야 (시뮬레이터 기준): 첫 조커 8분, 조커 4칸 1시간 20분, 신화 해금 3시간, 마지막 조커 8시간, 도감 400개는 그보다 한참 뒤.

## 폴더

| 폴더 | 내용 |
| --- | --- |
| `src/` | 데이터팩 생성기 (파이썬) |
| `src/hands.py` | 족보 400개의 이름 · 조건 · 판정식 |
| `src/engine.py` | 족보 판정 함수 생성 (숫자 하나에 명령 370개쯤) |
| `src/sys_*.py` | 굴리기 · 화면 · 미션 · 도감 · 도전과제 |
| `src/jokers.py`, `src/adv.py`, `src/common.py` | 조커, 도전과제, 값 · 가격 |
| `src/tiers.json` | 숫자 10억 개를 전부 세서 얻은 족보별 확률 |
| `tools/` | 검사 · 분석 도구 |
| `base/` | 리뉴얼 전(v201) 데이터팩 |
| `dice_roll.zip` | 완성된 데이터팩 |

## 빌드

```
python3 src/build.py OUT          # OUT/dice_roll, OUT/dice_roll.zip, OUT/hands.json
```

## 검사

| 도구 | 하는 일 |
| --- | --- |
| `tools/testgen.py` + `engtest` | 판정 함수를 C로 옮겨서 따로 짠 기준(`src/ref.h`)과 비교. 10억 개 전부 맞음 |
| `tools/count.c`, `tools/mktiers.py` | 10억 개를 세서 확률 · 등급 · 코인 정하기 |
| `tools/cointest.py` | 코인 계산(조커 · 강화 · 부스트, 큰 수)을 C로 옮겨 식과 비교 |
| `tools/sim.c`, `tools/simgen.py`, `tools/advcal.py` | 처음부터 끝까지 플레이하는 시뮬레이터 — 가격과 보상 맞추기 |
| `tools/nrtest.py`, `tools/nrbot.py` | 진짜 26.3 서버에 가짜 플레이어로 들어가서 굴리기 · 상점 · 조커 · 미션 · 화면 시험 |
| `tools/handsdoc.py` | `HANDS.md` 만들기 |

```
python3 tools/testgen.py WORK src/tiers.json && gcc -O1 -Isrc -IWORK -o WORK/engtest WORK/engtest.c
WORK/engtest 0 1000000000 1 1 1 50              # 전부 (30분쯤)
python3 tools/cointest.py OUT/dice_roll WORK
python3 tools/simgen.py WORK && gcc -O2 -Isrc -IWORK -o WORK/sim tools/sim.c && WORK/sim 10 1 1
MCSRV=서버폴더 python3 tools/nrtest.py OUT
```

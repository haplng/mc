# 배드워즈 타이쿤

마인크래프트 자바 26.3용 데이터팩. 공허 월드에 로비 1개와 8팀 배드워즈 맵 5개를 깔고, 기지마다 상점 NPC 2명을 세운다.
디스플레이 엔티티는 쓰지 않는다. 지금 들어 있는 건 **건축 + 아이템 상점**까지고, 자원 생성기·코인·AI 같은 게임 진행은 아직 없다.

![미리보기](preview.png)

## 들어 있는 것 (v7)

| # | 맵 | 크기 | 중심 (x, z) | 팀 기지 | 상점 NPC 자리 |
| --- | --- | --- | --- | --- | --- |
| 1 | 티타임 | 137x137 | 600, 0 | 받침 접시 위 찻잔 | 찻잔 벽 안쪽 틈 (고리 블록이 계산대) |
| 2 | 체스 | 157x157 | 1000, 0 | 체크 타일 위 룩 탑 | 탑 벽 아래 홈 |
| 3 | 서커스 | 177x177 | 1400, 0 | 줄무늬 천막 | 천막 안 매표소 |
| 4 | 도서관 | 223x223 | 1800, 0 | 쌓인 책 위 책 집 | 책장 벽감 |
| 5 | 태양계 | 267x267 | 2200, 0 | 고리 행성 위 유리 돔 | 돔 안 기둥 사이 |

- 로비는 0, 0. 성벽의 문 5개가 맵으로 가는 입구고, 스폰 광장 서쪽 오두막이 **업그레이드 가게**다 (코인으로 상점 물건을 해금할 자리. 지금은 안내 창만 뜬다).
- 기지마다 `아이템 상점`, `팀 업그레이드` NPC가 건물 안에 한 명씩 있다 (움직이지 않고 맞지도 않는 주민). 크리에이티브로 때리거나 `/kill` 로 없어져도 5초 안에 다시 생긴다.

## 아이템 상점

`아이템 상점` NPC를 우클릭하면 창이 뜬다. 위쪽이 분류 8개(빠른 구매, 블록, 근접 무기, 방어구, 도구, 원거리, 물약, 유틸리티), 아래가 물건이다.

- 물건을 누르면 인벤토리의 철 / 금 / 에메랄드로 바로 산다. 살 수 있으면 가격이 초록, 모자라면 빨강으로 보인다.
- 양털·테라코타·방폭 유리는 그 기지의 팀 색으로 나온다.
- 갑옷은 레깅스와 부츠를 바로 입혀 주고, 곡괭이와 도끼는 살 때마다 한 단계씩 오른다. 가위는 한 번만 살 수 있다.
- 가격은 하이픽셀 기준 (양털 16개 철 4, 돌 검 철 10, 철 검 금 7, 다이아 검 에메랄드 4 …). 전부 `gen3/shop.py` 의 `ITEMS` 표에 있다.
- 빈대, 드림 디펜더, 화염구, TNT, 다리 알, 마법 우유, 팝업 타워는 물건만 나오고 특수 효과는 아직 없다.
- 생성기가 아직 없어서 자원은 직접 꺼내야 한다. 시험용: `/function bw:shop/money` (철 64, 금 32, 에메랄드 16).

26.3의 대화 상자(dialog)로 만든 창이다. 상자 모양 GUI는 바닐라에서 NPC 우클릭으로 열 수 없다.
버튼은 `/trigger bw.buy`, `/trigger bw.shop` 을 보내고, 창을 그릴 때마다 매크로 함수가 그 플레이어의 자원·도구 단계를 넣어서 새로 만든다.

## 설치

- `datapack/bedwars_maps.zip` 을 월드의 `datapacks` 폴더에 넣고 월드에 들어가면 알아서 설치된다.
- 예전 버전이 깔려 있던 월드면 맵을 지우고 새로 깐다 (1~2분, 그동안 플레이어는 로비에 모아 둔다). 손으로 고친 블록은 이때 사라진다.
- 다시 깔기: `/function bw:reinstall`. 로비로 돌아오기: `/trigger lobby`.
- 새 공허 월드 폴더 만들기: `python3 gen/world.py <saves 폴더> datapack/bedwars_maps.zip` (`BW_TEMPLATE` 에 26.3 월드 하나의 level.dat 과 data/minecraft/*.dat 필요).

## 게임 로직용 태그

맵마다 marker 엔티티가 들어 있다 (태그 `bw`).

| 태그 | 맵당 개수 | 위치 |
| --- | --- | --- |
| `bw.spawn` | 8 | 팀 스폰 |
| `bw.bed` | 8 | 침대 |
| `bw.gen.iron` | 8 | 팀 생성기 |
| `bw.gen.diamond`, `bw.gen.emerald` | 4씩 | 다이아 / 에메랄드 생성기 |
| `bw.shop`, `bw.upgrade` | 8씩 | 상점 / 팀 업그레이드 NPC 자리 |

팀 마커와 NPC에는 `bw.t.<색>` (red, blue, lime, yellow, cyan, white, pink, gray) 이 붙는다.
NPC는 `bw.npc` + `bw.npc.shop` / `bw.npc.upgrade` / `bw.npc.unlock`(로비) 주민이다.

## 빌드

```
pip install nbtlib numpy scipy pillow
python3 gen3/pack.py            # out3/ 에 데이터팩, 미리보기, maps.json
python3 gen3/run.py m01_tea     # 맵 하나만 (부품만: run.py m01_tea cup_base:red)
```

- `gen3/canvas.py`, `gen3/kit.py` 블록 캔버스와 도형·섬·나무·가구·침대·마커
- `gen3/m01_tea.py` `m02_chess.py` `m03_circus.py` `m06_library.py` `m09_solar.py` 맵 하나씩 (`gen3/unused/` 는 뺀 맵 5개)
- `gen3/lobby.py` 로비, `gen3/shop.py` 아이템 상점, `gen3/pack.py` 설치 함수와 데이터팩
- `gen3/check.py` 블록 상태·떠 있는 블록·마커·걸어서 닿는지 검사 (`ref/263_blocks_data.json` 사용)
- `tools/verify4.py <월드>` 서버에 깔린 블록이 설계와 하나하나 같은지, `tools/shoptest.py` 가짜 플레이어로 NPC 우클릭·전 품목 구매·모든 분류를, `tools/npctest.py` NPC 81명이 제자리에 한 명씩 있는지 확인
  (26.3 테스트 서버와 `steve-eokka/tools` 의 rcon·bot 을 쓰고, 경로는 작업 환경 기준이다)

26.3은 어드밴스먼트 같은 등록 데이터에 오류가 있으면 월드가 아예 안 열린다. 엔티티 조건은 `minecraft:entity_type`, `minecraft:entity_tags` 처럼 하위 조건 맵으로 쓴다.

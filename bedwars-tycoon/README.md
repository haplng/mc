# 배드워즈 타이쿤 (맵 + 로비)

마인크래프트 자바 26.3용. 떠 있는 섬 형식의 8팀 배드워즈 맵 10개와 로비 1개를 데이터팩 하나로 설치한다.
공허 월드에서 쓰는 걸 기준으로 만들었다. 디스플레이 엔티티는 쓰지 않고, 생성기·상점 같은 게임 시스템은 아직 없이 건축만 들어 있다.

![미리보기](preview.png)

## 설치

- 새 공허 월드: `python3 gen/world.py <saves 폴더> out/bedwars_maps.zip` (BW_TEMPLATE 에 26.3 월드 하나의 level.dat 과 data/minecraft/*.dat 이 있어야 함).
  처음 들어가면 로비부터 깔리고 그동안 천천히 떨어지기가 걸린다. 30초쯤이면 맵 10개까지 다 깔린다.
- 이미 있는 월드: `datapack/bedwars_maps.zip` 을 `datapacks` 폴더에 넣고 `/reload`. 다시 깔려면 `/function bw:install/start`.
- 로비 문으로 들어가면 그 맵의 빨강팀 스폰으로 이동. 로비로 돌아오기: `/trigger lobby` (또는 `/function bw:lobby`).

## 위치 (밑판 높이 y=64)

| 맵 | 크기 | 중심 |
| --- | --- | --- |
| 로비 | 178x158 | 0, 0 |
| 1. 벚꽃 정원 | 189x189 | 600, 0 |
| 2. 사막 오아시스 | 195x195 | 1000, 0 |
| 3. 얼음 마을 | 211x211 | 1400, 0 |
| 4. 버섯 숲 | 217x217 | 1800, 0 |
| 5. 등대 항구 | 223x223 | 2200, 0 |
| 6. 가을 농장 | 233x233 | 2600, 0 |
| 7. 네더 요새 | 239x239 | 3000, 0 |
| 8. 정글 신전 | 247x247 | 3400, 0 |
| 9. 천공의 성 | 255x255 | 3800, 0 |
| 10. 엔드 성채 | 265x265 | 4200, 0 |

## 게임 로직용 마커

모든 맵에 보이지 않는 marker 엔티티가 들어 있다 (태그 `bw`).

| 태그 | 개수 | 위치 |
| --- | --- | --- |
| `bw.spawn` | 8 | 팀 스폰 |
| `bw.bed` | 8 | 침대 |
| `bw.gen.iron` | 8 | 팀 철/금 생성기 |
| `bw.gen.diamond` | 4 | 다이아 생성기 |
| `bw.gen.emerald` | 4 | 에메랄드 생성기 (가운데 섬) |
| `bw.shop`, `bw.upgrade` | 8씩 | 상점 / 팀 업그레이드 NPC 자리 |

팀 마커에는 `bw.t.<색>` (red, blue, lime, yellow, cyan, white, pink, gray) 태그가 붙어 있다. 좌표는 `datapack/maps.json`.

## 빌드

```
pip install nbtlib numpy scipy pillow
python3 gen/pack.py          # out/ 에 데이터팩 + 미리보기 생성
```

- `gen/parts.py` 섬, 나무, 바위, 지붕 같은 부품
- `gen/themes.py` 맵 10개의 테마 (블록 구성, 집, 가운데 섬 건물)
- `gen/bwmap.py` 배치: 팀 기지 8개 (가운데에서 침대까지 84~120칸), 다이아 섬 4개, 장식 섬 4개, 가운데 섬. 섬 사이 가장 가까운 틈 20~30칸
- `gen/interior.py` 집 안 가구, 팀 생성기 위 대장간, 다이아·에메랄드 생성기 사당
- `gen/mids.py` 가운데 섬 건물 (탑, 피라미드 보물방, 얼음 성, 등대, 풍차, 네더 탑, 정글 신전, 성 알현실, 엔드 탑) 안쪽까지
- `gen/world.py` 공허 월드 폴더 만들기
- `gen/lobby.py` 로비
- `gen/check.py` 모든 블록 상태를 26.3 블록 목록(`ref/`)으로 검사, 마커 주변이 비어 있는지 검사
- `tools/oldanvil.py`, `tools/summ.py` 참고 맵(1.8 월드) 분석용

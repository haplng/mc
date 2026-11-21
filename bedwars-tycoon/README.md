# 배드워즈 타이쿤 (맵 + 로비)

마인크래프트 자바 26.3용. 떠 있는 섬 형식의 8팀 배드워즈 맵 10개와 로비 1개를 데이터팩 하나로 설치한다.

![미리보기](preview.png)

## 설치

1. `datapack/bedwars_maps.zip` 을 월드의 `datapacks` 폴더에 넣는다.
2. 게임 안에서 `/reload`. 처음 한 번은 알아서 설치된다 (1분쯤). 다시 깔려면 `/function bw:install/start`.
3. 로비 문으로 들어가면 그 맵의 빨강팀 스폰으로 이동. 로비로 돌아오기: `/trigger lobby` (또는 `/function bw:lobby`).

## 위치 (밑판 높이 y=64)

| 맵 | 크기 | 중심 |
| --- | --- | --- |
| 로비 | 178x158 | 0, 0 |
| 1. 벚꽃 정원 | 147x147 | 600, 0 |
| 2. 사막 오아시스 | 153x153 | 1000, 0 |
| 3. 얼음 마을 | 169x169 | 1400, 0 |
| 4. 버섯 숲 | 175x175 | 1800, 0 |
| 5. 등대 항구 | 183x183 | 2200, 0 |
| 6. 가을 농장 | 193x193 | 2600, 0 |
| 7. 네더 요새 | 197x197 | 3000, 0 |
| 8. 정글 신전 | 207x207 | 3400, 0 |
| 9. 천공의 성 | 217x217 | 3800, 0 |
| 10. 엔드 성채 | 225x225 | 4200, 0 |

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
- `gen/bwmap.py` 배치: 팀 기지 8개 (침대 거리 62~98칸), 다이아 섬 4개, 가운데 섬
- `gen/lobby.py` 로비
- `gen/check.py` 모든 블록 상태를 26.3 블록 목록(`ref/`)으로 검사, 마커 주변이 비어 있는지 검사
- `tools/oldanvil.py`, `tools/summ.py` 참고 맵(1.8 월드) 분석용

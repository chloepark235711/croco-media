# Croco 얼굴 참조 — v2 (오너 지시 2026-11-12 20:33 MST: "이렇게 생겨야해")

오너가 초기 영상 3편 스크린샷(Red, Yellow, Blue / A Little Fish Surprise / Croco Found a Strawberry)을 보내며 이 모습으로 지정.
특징: 연한 연두빛 초록 몸, 넓고 둥근 큰 머리, 크고 둥근 갈색 눈(흰자 넓음), 진한 분홍 볼, 크림/노란 배·턱 아래,
짧고 넓은 주둥이(위쪽 콧구멍 2개), 주황 멜빵 + 구멍 4개 나무 단추 + 노란 별 주머니.

| 파일 | 용도 | 출처 | 크롭(1320x2868 원본 기준) | sha256 |
|---|---|---|---|---|
| reference/croco-face.png | 1순위 (정면, 입 다묾) | "Red, Yellow, Blue!" 스크린샷 (IMG_1251) | x0 y717 w1320 h1003 | `fc7d52460e1c992f0083a8477c82287732f4c34b359ea3f5590ae2587b290141` |
| reference/croco-face-2.png | 2순위 (3/4 측면, 전신 상반·멜빵·별·단추) | "A Little Fish Surprise!" 스크린샷 (IMG_1252) | x573 y803 w747 h917 | `c541d59a124bdd22dc1e4fc199abd462e5f59147f70baf8f5b49958f9bb8f6a6` |

- 주의: croco-face-2.png 원본에는 **작은 이빨이 보임**. 하드 룰(치아 없음)은 그대로 유지 — 프롬프트 NEG 그대로, QA에서 치아 보이면 FAIL.
- 사용: kling-video/v4.0/reference-to-video `image_urls` = [croco-face.png, croco-face-2.png]. 텍스트 프롬프트는 변경 없음.
- 이전 v1(Oops! Saying Sorry 7.2초)은 reference/archive-croco-face-oops-v1.png 로 보관, 사용 안 함.
- 오너 지시 없이 변경 금지.

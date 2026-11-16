# Croco 제작 실패 원인 분류 / 재발 방지 (자동 학습 기록)
갱신: 2026-11-16. 검증된 개선만 다음 제작에 반영. 디자인·품질 기준은 자동 완화하지 않음.

## 실패 유형 (taxonomy)
| 코드 | 유형 | 수정 가능? | 조치 |
|---|---|---|---|
| T1 | 이빨/입 (이빨 줄, 큰 입 벌림) | 참조·프롬프트 원인이면 가능 | preflight 1·2에서 사전 차단 |
| F1 | 얼굴 불일치 (노안, 긴 얼굴, 작은 눈) | 참조 이미지 사용으로 대부분 해결 | croco-face.png 참조 필수 |
| O1 | 의상 (멜빵·별·단추 누락/변형) | 재시도 | LOCK 원문 필수 (preflight 3) |
| C1 | 내용 (학습 목표 동작 불명확, 모양 오류 등) | 장면 문구 수정 후 재시도 | 같은 문구 반복 금지 |
| P1 | Pebble (색·점 개수·옷·이빨) | 재시도 | PEBBLE_LOCK 원문 |
| B1 | 예산 / 비용 불확실 | — | preflight 6, 실행 안 함 |
| A1 | API/권한/연결 (401/403/CONNECT) | — | BLOCKED, 우회 금지 |

## 레슨 (증거 포함)
- **L1** croco-face-2.png 원본에 위턱 작은 이빨 4개 → 참조로 쓰면 이빨 줄 4–8개 복사. 11-13 6개 중 5개, 11-16 4개 중 4개 FAIL ($2.01). → **생성 참조 금지** (오너 2026-11-16).
- **L2** 긍정 프롬프트의 "smile showing two tiny teeth" 같은 이빨 요청은 개수 제어가 안 됨 ("exactly two"는 무시됨). → 긍정부에 teeth 단어 금지, MOUTH = 입 다문 미소 문장.
- **L3 (검증된 성공 조합)** croco-face.png 단독 + brand.py CHARACTER_LOCK (closed-mouth) + "closed-mouth smile" 문구: 11-14 8개 중 이빨 FAIL 2개(잘라냄/재시도 해결), 11-16 v4 3/3 이빨 0개.
- **L4** 장면 끝 "happy smiles / look at the camera"는 크게 벌린 입으로 흐름 (11-16 S3). "gentle closed-mouth smile(s)"로 바꾸면 3/3 입 다묾.
- **L5** 같은 원인으로 2회 실패하면 추가 과금 중단 → 오너 결정 요청 (11-16 v1: 4건 후 중단).

## 성공 vs 실패 프롬프트 차이 (11-16 같은 장면, 같은 모델/길이)
| 항목 | 실패 (v1, 4/4 FAIL) | 성공 (v4, 3/3 PASS) |
|---|---|---|
| 참조 | croco-face-2.png + croco-face.png | croco-face.png |
| LOCK 입 | "sweet happy smile showing two tiny rounded ivory baby teeth" | "gentle closed-mouth smile with no visible teeth" |
| MOUTH | "exactly two tiny ... teeth" | "closed-mouth smiles for both characters, no teeth visible at any time." |
| 장면 미소 | "sweet smile", "kind smile", "happy smiles" | "gentle/kind closed-mouth smile(s)" |
| NEG | "no more than two teeth" | "no teeth, no open mouth with teeth" + "no wide-open mouth" |

# 자동화 운영 (공개용 설명서)
| 시각 | 작업 | 하는 일 | 하지 않는 일 |
|---|---|---|---|
| 17:00 | 마케팅 | 트렌드 조사 → 다음 날 2편을 `PLANNED`로 기록 → `plan_check` 통과 확인 | 생성, 게시 |
| 20:00 | Claude Code V2 | `python3 -m croco.generate --date <내일> --live` (승인 없으면 자동 차단) | 편집, 게시 |
| 08:00 | 제작 | `GENERATED`만 처리: inbox의 clips 다운로드·SHA256 확인 → 편집 → QA → `publish_guard` 통과 시 Metricool 공개 예약 | 영상 생성 |

예산 승인·지출 원장·오류 로그는 **비공개 저장소 croco-control**에만 있습니다 (이 저장소에 없음).
각 작업 프롬프트 초안은 `prompts.md`.

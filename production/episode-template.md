# 에피소드 기록 형식
파일: `briefings/episodes/YYYYMMDD-NN.json` (하루 2편: -01, -02). 마케팅팀이 `PLANNED`로 작성.
```json
{
  "id": "20261105-01", "date": "2026-11-05", "status": "PLANNED",
  "title": "...", "description": "...", "tags": ["kids", "..."],
  "learning_goal": "나눔의 기쁨", "topic_key": "sharing-toys",
  "scenes": [{"n": 1, "prompt": "Croco, a green baby crocodile with a yellow belly and red scarf, ...", "duration": 5}]
}
```
상태: PLANNED → GENERATING → GENERATED → EDITED → QA_PASSED → SCHEDULED.
실패/중단: SKIPPED_BUDGET, FAILED, NEEDS_REVIEW, QA_FAILED. 금액·승인 정보는 넣지 않습니다.
검증: `python3 -c "from croco import episodes,json..."` 대신 `python3 -m croco.plan_check YYYY-MM-DD`.

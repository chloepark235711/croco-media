# 에피소드 기록 형식
파일: `briefings/episodes/YYYYMMDD-NN.json`. 하루 **활성 2편**(HOLD는 개수에 넣지 않음). ID는 한 번 쓰면 재사용 금지(HOLD 포함).
작성: 17:00 부서 회의(교육콘텐츠부·트렌드리서치부) → Claude 프로젝트 `pipeline/v2-episodes/<id>.json` → 20:00 V2 작업이 main에 반영.
실제 예시: `briefings/episodes/20261105-02.json`, `20261105-03.json`.

필수 필드: `id`, `date`(게시일 D), `status: "PLANNED"`, `title`, `description`, `tags`(5–10), `hashtags`(3–5, `#CrocosLittleWorld` 포함),
`made_for_kids: true`, `learning_goal`, `topic_key`(고유), `source_episode`(EP-xxxx, 고유), `character_lock`(= `croco/brand.py` CHARACTER_LOCK 글자 그대로),
`scenes`(1–3개, `{"n", "prompt", "duration": 3–5 정수}`), `captions`, `safety`.
자동 기록 필드: `requests`, `sha256`, `asset_paths`, `qa_status`, `qa_checklist`, `scheduled_slot`, `final_sha256`, `metricool_post_id`, `youtube_post_id`.

상태: PLANNED → GENERATING → GENERATED → EDITED → QA_PASSED → SCHEDULED → PUBLISHED.
실패/중단: SKIPPED_BUDGET, FAILED, NEEDS_REVIEW, QA_FAILED. **HOLD**(소유자 결정: 재제출·폴링·편집·게시 모두 금지).
금액·승인 정보는 넣지 않습니다. 검증: `python3 -m croco.plan_check YYYY-MM-DD` 가 `OK`여야 합니다.

# 작업 프롬프트 초안 / 필요한 설정 (대표 확인용 — 예약 작업은 대표가 직접 수정)

## 20:00 V2 생성 (trig "Croco 20:00 Higgsfield 생성 V2 (Claude Code)")
현재 이 작업은 **검증 전용** 프롬프트입니다(http_api로 생성되어 에이전트가 수정 불가). 실제 생성을 켜려면 대표가 아래로 교체:

> You are the 20:00 V2 generation worker of Croco's Little World. Dates: T = America/Denver today, D = T + 1.
> 1. add_repo chloepark235711/croco-media (push), clone main. If push is refused, stop and report.
> 2. With the Projects tool read pipeline/v2-episodes/*.json. Copy each file whose date == D, status == "PLANNED"
>    and whose id is not yet in briefings/episodes/ into briefings/episodes/ unchanged. Never overwrite an existing record.
> 3. Run `python3 -m croco.plan_check D`. Only if it prints OK: commit "plan D" and push to main.
>    If it is not OK, push nothing and report the problems.
> 4. Run `python3 -m croco.generate --date D` (dry run, $0) and report its APPROVAL line and estimate.
> 5. Only if the dry run says "APPROVAL: valid": run `python3 -m croco.generate --date D --live`.
>    Env: CROCO_CONTROL_REMOTE must be reachable. Never edit approvals/, never resubmit HOLD/NEEDS_REVIEW/GENERATING
>    episodes, never reuse an old request id, never print credentials.
> 6. Report in Korean: episodes, statuses, request ids, inbox commit. A finished run is not a publication.

## 08:00 제작 — 코드 호출 변경 (V2 코드가 main에 병합된 뒤 적용)
- `mark_qa(pub, id, passed, notes, checklist=...)` — passed=True는 `croco.qa.REQUIRED` 10개 항목이 모두 True일 때만 허용.
- `claim_publish(pub, id, slot, final_sha256)` — slot은 `croco.slots.next_free_slot(occupied)`의 값(예: `2026-11-06T12:00`).
  occupied = 기존 Metricool 예약(테스트 게시물 제외, `slots.is_test_post`) + `slots.occupied_from_episodes`.
- Metricool 예약 성공 → `record_metricool(pub, id, post_id, uuid)`. 실패·애매 → `publish_failed(pub, id, reason)` (재시도 금지).
- Metricool에서 PUBLISHED + YouTube ID 확인 후에만 `record_published(pub, id, youtube_id)`.
- 예약 시각: `slots.metricool_datetime(slot)` → (`YYYY-MM-DDTHH:MM:00`, `America/Denver`).

## 17:00 부서 회의 — 변경 없음
V2 export 5번(활성 2편, 최대 3장면, 하루 30초, 고정 블록 글자 그대로)은 이미 이 코드의 검사 규칙과 같습니다.

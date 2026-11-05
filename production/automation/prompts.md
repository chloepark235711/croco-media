# 예약 작업 최종 프롬프트 / 설정 (대표가 직접 붙여 넣기)

에이전트는 예약 작업을 수정하지 않았습니다. 아래는 **main 병합 후** 붙여 넣을 최종본입니다.
병합 전에 붙이면 main에 코드가 없어 작업이 실패합니다(안전하게 멈춤).

## 0. 실행 환경별 확인 결과 (2026-11-05 기준, 실제 실행 기록 근거)
| 작업 | croco-media 쓰기 | croco-control | Higgsfield | Metricool | 근거 |
|---|---|---|---|---|---|
| 17:00 부서 회의 (trig_01G4WVt8…) | ❌ push 403 | ❌ | 불필요 | ✅ 커넥터 | 11/4 실행 기록 |
| 20:00 V2 (trig_01WGNdTY…) | ⚠️ 저장소는 복제됨, 쓰기 미검증 | ⚠️ 미검증 | ✅ 프록시 경로 연결 / MCP 잔액 조회 | ✅ 커넥터 | 11/5 03:06Z 검증 실행 |
| 08:00 제작 (trig_01MRGWbX…) | ❌ push 403 | ❌ | 불필요(❌ 403) | ✅ 커넥터 | 11/5 09:37 MT 실행 기록 |

**대표 설정 작업 (claude.ai/code/routines → 각 작업 → 저장소/환경):**
1. 17:00, 08:00 작업에 저장소 `chloepark235711/croco-media`를 **쓰기 권한**으로 추가.
2. 20:00 V2 작업에 `chloepark235711/croco-media`(쓰기)와 `chloepark235711/croco-control`(쓰기: ledger/errors/requests만) 추가.
3. 17:00 → 20:00 계획 전달은 **GitHub main** 하나로 통일합니다(V2 작업에는 Claude 프로젝트 도구가 없음).

---

## 1. 17:00 부서 회의 — 기존 프롬프트 5번(V2 export)을 아래로 교체
> 5. V2 handoff (owner order 2026-11-05). For tomorrow D (America/Denver), make sure exactly 2 ACTIVE episodes
> exist on chloepark235711/croco-media **main** in briefings/episodes/<id>.json (HOLD does not count).
> Attach the repo with add_repo (push) and clone main. If push access is refused, write the two JSON files to the
> Claude project pipeline/v2-episodes/ instead, report "17:00 → GitHub 전달 실패 (권한)" and stop this step.
> Format = production/episode-template.md. Rules: new id YYYYMMDD-NN never used before (check every file in
> briefings/episodes/, HOLD included); status "PLANNED"; date D; target_slot "D T12:00" for one and "D T17:00" for
> the other; 1–3 scenes, integer duration 3–5 s, total ≤ 30 s for the day; every scene prompt built exactly like
> croco/brand.py scene_prompt() (Croco lock verbatim [+ Pebble lock] + " Scene: …" + Mouth line + "\nNegative: " +
> standard negative); character_lock = croco/brand.py CHARACTER_LOCK; unique topic_key and source_episode;
> English title "<short sentence>! <emoji> | Croco's Little World #Shorts", description, 5–10 tags, 3–5 hashtags
> incl. #CrocosLittleWorld, made_for_kids true, learning_goal, captions, safety.
> Never edit a record whose status is not PLANNED. Run `python3 -m croco.plan_check D`; push to main ONLY if it
> prints OK, with commit message "plan D". Otherwise push nothing and list the problems in the briefing.

## 2. 20:00 V2 생성 — 전체 교체 (trig_01WGNdTYBGgM6wpLZgeNJYNH, 에이전트 수정 불가 작업)
> You are the 20:00 V2 generation worker of Croco's Little World. Internal report in Korean.
> Dates: T = America/Denver today (spend day), D = T + 1 (publish day). Never print or store credentials.
> Never create, edit or delete scheduled tasks, Metricool posts or croco-control approvals/ or reconcile/.
> 1. Access: add_repo chloepark235711/croco-media (push) and chloepark235711/croco-control (push); clone both.
>    If either is refused, stop: report which one and do nothing else.
> 2. Plans: on croco-media main run `python3 -m croco.plan_check D`. If it is not OK, do not generate; report.
> 3. Dry run ($0): `CROCO_CONTROL_REMOTE=https://github.com/chloepark235711/croco-control python3 -m croco.generate --date D`.
>    Report every line. Continue to step 4 ONLY if the output contains "APPROVAL: valid" and no "UNCONFIRMED COST"
>    line and no ERROR line.
> 4. Paid run: same command with `--live`. Never run it twice in one session. The code itself refuses HOLD,
>    re-submission, unverified approvals, unconfirmed costs and anything above $5.00/day.
> 5. If an episode ends NEEDS_REVIEW / FAILED / STILL GENERATING: do not retry by hand. Report the failure block:
>    step, episode_id, exact error, external actions already done (request ids), spend confirmed or not,
>    whether the next run resumes automatically, and what the owner must approve.
> 6. Report in Korean: per episode status, request ids, estimated spend vs $5.00, inbox commit, croco-control commit.
>    Generated clips are not published videos.

## 3. 08:00 제작 — Intake·QA·게시 단계를 아래 코드 호출로 교체 (나머지 마케팅 부록 M0–M6 유지)
> Intake: add_repo croco-media (push), clone main. Select episodes with status GENERATED (never HOLD/test).
> For each: verify inbox clips/<date>/<id>/manifest.json sha256 for every scene; then
> `publish_guard.claim_edit(pub, id)` (double-processing lock) → edit/render → inspect the real file.
> QA: build a checklist dict over croco.qa.REQUIRED. Set an item True ONLY if you actually checked it on the
> rendered file (ffprobe/full decode, frames viewed, loudness measured, copyright/safety reviewed); False if it
> failed; leave it out if you could not check it (it is recorded as UNVERIFIED and blocks publishing).
> Call `publish_guard.mark_qa(pub, id, passed, notes, checklist=checklist)` with passed = croco.qa.evaluate(checklist)[0].
> Never set items True to make QA pass.
> Publish (only if 07 says PUBLISHING_ENABLED: yes and status QA_PASSED):
>  a. getScheduledPosts (brand 7808692, America/Denver) for today..+7 days; occupied = their 12:00/17:00 slot keys,
>     excluding posts where croco.slots.is_test_post(text or title) is true.
>  b. slot = `publish_guard.choose_slot(pub, id, occupied_external=occupied)` (target_slot if free and ≥30 min ahead,
>     else the next free slot — never a past slot).
>  c. `publish_guard.claim_publish(pub, id, slot, final_sha256)` BEFORE calling Metricool.
>  d. Relay upload as before; createScheduledPost at `croco.slots.metricool_datetime(slot)`, youtube short, public,
>     madeForKids true, category EDUCATION, draft false, autoPublish true, title/description/tags/hashtags from
>     the episode record.
>  e. Success → `publish_guard.record_metricool(pub, id, post_id, uuid)`; reset relay.
>     Error or unclear result → FIRST call getScheduledPosts for that slot; if the post exists, record_metricool;
>     if it does not exist or you cannot tell → `publish_guard.publish_failed(pub, id, reason)` (no retry).
>  f. Later runs: when Metricool shows the post PUBLISHED with a YouTube video id →
>     `publish_guard.record_published(pub, id, youtube_id)` and record https://youtube.com/shorts/<id>.
>     A Metricool schedule is NOT a publication.

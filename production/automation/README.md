# 자동화 운영 (V2, 공개용 설명서)
모든 시각은 America/Denver. 목표: 매일 **12:00, 17:00**에 서로 다른 키즈 Shorts 2편 자동 공개.

| 시각 | 작업 | 하는 일 | 하지 않는 일 |
|---|---|---|---|
| 17:00 | 부서 회의 | 다음 날(D) 활성 2편을 PLANNED JSON으로 작성 (Claude 프로젝트 `pipeline/v2-episodes/`) | 생성, 게시, GitHub push(권한 없음) |
| 20:00 | V2 생성 | 계획을 main에 반영 → `plan_check D` → `generate --date D` dry-run → 승인 유효 시 `--live` | 편집, 게시 |
| 08:00 | 제작·품질·게시 | D의 `GENERATED`만: inbox SHA256 검증 → 편집 → QA 체크리스트 → `publish_guard` → Metricool 예약(12:00/17:00, draft=false) | 영상 생성 |

```
PLANNED ─20:00─▶ GENERATING ─▶ GENERATED ─08:00─▶ EDITED ─▶ QA_PASSED ─▶ SCHEDULED ─(Metricool PUBLISHED)─▶ PUBLISHED
   │                  │                                 └─▶ QA_FAILED (게시 차단)
   ├─▶ SKIPPED_BUDGET └─▶ NEEDS_REVIEW / FAILED (재제출 없음, 예산 보류)
HOLD: 소유자 결정. 제출·재제출·폴링·편집·게시 모두 없음. 하루 2편 슬롯에 넣지 않음.
```

## 중복 방지 (episode_id 기준)
- 생성: `PLANNED → GENERATING` 전환이 CAS 커밋이라 한 워커만 제출. 재실행 시 GENERATING은 **폴링만**, 제출 기록 불완전/애매하면 NEEDS_REVIEW(재제출 없음).
- 계획: `topic_key`, `source_episode` 중복 거부 (HOLD 포함 전체 기록 대상).
- 게시: `claim_publish`가 QA_PASSED·게시 ID 없음·슬롯 미점유·최종 파일(sha256)/원본 클립 미사용을 한 커밋에서 확인.
  YouTube ID는 `record_published`로 한 번만 기록.

## 예산
- 하루 $5.00 (America/Denver **지출일** 기준, 모든 실행 공유). 비공개 croco-control의 `approvals/budget.json`이 유효해야만 예약·제출.
- 승인 파일이 없거나, 만료·비활성이거나, 봇이 수정했으면 → `BLOCKED`, 유료 요청 0건.
- 견적 × 1.1(여유분)로 예약 후 제출. 거절·실패 시 예약은 **보류**(대표가 `reconcile/<id>.json`으로만 해제).

예산 승인·지출 원장·오류 로그는 **비공개 저장소 croco-control**에만 있습니다.
각 작업 프롬프트 초안과 필요한 설정은 `prompts.md`, 병합 절차는 `MERGE_PLAN.md`.

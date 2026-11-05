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

## 상태 전이 (요청서 예시와 실제 구현 대응)
| 요청서 | 실제 상태 | 누가/언제 |
|---|---|---|
| PLANNED | PLANNED | 17:00 계획 (plan_check OK 후 main) |
| APPROVED | (별도 상태 없음) PLANNED + 검증된 예산 승인 + 미확정 비용 없음 | 20:00 시작 시 코드가 확인 |
| GENERATING | GENERATING | 20:00, CAS로 한 워커만 |
| GENERATED | GENERATED | 20:00 (sha256·asset_paths 기록) |
| QA_PENDING | EDITED | 08:00 claim_edit |
| QA_PASSED | QA_PASSED / QA_FAILED | 08:00 mark_qa (체크리스트 PASS/FAIL/UNVERIFIED) |
| SCHEDULED | SCHEDULED | 08:00 claim_publish → Metricool → record_metricool |
| PUBLISHED | PUBLISHED | Metricool에서 YouTube ID 확인 후 record_published |
| HOLD / FAILED / NEEDS_REVIEW | 동일 + SKIPPED_BUDGET | 재제출·자동 재시도 없음 |

모든 상태는 GitHub(공개 기록: croco-media main, 비용·요청: croco-control)에 커밋되므로 세션이 끝나도 다음 실행이 이어서 진행합니다.

## 중복 방지 (episode_id 기준)
- 생성: `PLANNED → GENERATING` 전환이 CAS 커밋이라 한 워커만 제출. 재실행 시 GENERATING은 **폴링만**, 제출 기록 불완전/애매하면 NEEDS_REVIEW(재제출 없음).
- 계획: `topic_key`, `source_episode` 중복 거부 (HOLD 포함 전체 기록 대상).
- 게시: `claim_publish`가 QA_PASSED·게시 ID 없음·슬롯 미점유·최종 파일(sha256)/원본 클립 미사용을 한 커밋에서 확인.
  YouTube ID는 `record_published`로 한 번만 기록.

## 예산
- 하루 $5.00 (America/Denver **지출일** 기준, 모든 실행 공유). 비공개 croco-control의 `approvals/budget.json`이 유효해야만 예약·제출.
- 승인 파일이 없거나, 만료·비활성이거나, 봇이 수정했으면 → `BLOCKED`, 유료 요청 0건.
- 승인 파일은 **대표 GitHub 계정의 검증된 커밋**이어야 합니다(웹 UI 커밋은 자동 서명). 에이전트가 기록한 승인은 거부.
- 견적 × 1.1(여유분)로 예약 후 제출. 거절·실패 시 예약은 **보류**.
- 비용이 확인되지 않은 요청(HOLD/FAILED/NEEDS_REVIEW의 미정산 예약)이 있는 날은 추가 유료 생성 중단.
  대표가 croco-control `reconcile/<id>.json`에 `{"resolved":"charged","usd":"0.40"}` 또는 `{"resolved":"not_charged"}`를 커밋하면 해제.
- Higgsfield 응답에는 실제 청구액이 없어, 정상 완료분도 원장에는 견적 기준(`basis: estimate`)으로 기록됩니다.

예산 승인·지출 원장·오류 로그는 **비공개 저장소 croco-control**에만 있습니다.
각 작업 프롬프트 초안과 필요한 설정은 `prompts.md`, 병합 절차는 `MERGE_PLAN.md`.

# main 병합 계획 (복구 브랜치 recovery/v2-rebuild-20261105)
기준: 코드 브랜치 `claude/compassionate-bardeen-pqr25c`(9f87fdf). main(cc22452)은 조상이라 fast-forward 가능, inbox는 건드리지 않음.
1. 검토: `python3 -m unittest tests.test_system` 전부 통과, `python3 -m croco.plan_check 2026-11-06` OK.
2. 대표가 croco-control `approvals/budget.json`을 **본인 GitHub 계정(웹 UI)으로 직접 커밋** — 현재 파일은 에이전트 기록이라 코드가 거부.
3. 20261105-01 비용 확정: Higgsfield에서 실제 청구액 확인 후 `reconcile/20261105-01.json` 커밋 (확정 전 11/5 지출일은 차단).
4. 대표 승인 후 PR 병합. 병합 전에는 main에 코드가 없어 20:00/08:00이 이 코드를 쓰지 않음.
5. `prompts.md`대로 예약 작업 프롬프트·저장소 권한 설정.
6. 첫 실행은 dry-run (`python3 -m croco.generate --date <D>`, 비용 0) → 대표 승인 후 1편만 제한 실제 테스트.
7. 되돌리기: 병합 PR revert 한 번.

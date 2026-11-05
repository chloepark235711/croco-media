# main 병합 계획 (복구 브랜치 recovery/v2-rebuild-20261105)
기준: 코드 브랜치 `claude/compassionate-bardeen-pqr25c`(9f87fdf). main(cc22452)은 조상이라 fast-forward 가능, inbox는 건드리지 않음.
1. 검토: `python3 -m unittest tests.test_system` 전부 통과, `python3 -m croco.plan_check 2026-11-05` OK 확인.
2. 대표가 croco-control `approvals/budget.json`을 직접 확인/커밋(봇 수정 시 자동 거부). 없으면 유료 생성은 계속 차단됨.
3. 대표 승인 후 PR 병합(fast-forward). 병합 전에는 main에 코드가 없어 20:00/08:00이 이 코드를 쓰지 않음.
4. 병합 후 첫 실행은 dry-run: `python3 -m croco.generate --date <D>` (비용 0).
5. 되돌리기: 병합 PR revert 한 번(다른 파일 영향 없음).

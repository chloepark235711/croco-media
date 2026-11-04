# main 병합 계획 (코드 브랜치 claude/compassionate-bardeen-pqr25c)
변경은 **추가 파일만**(croco/, tests/, production/, README 갱신, .gitignore, briefings/episodes/.gitkeep, clips/.gitkeep). 기존 파일 삭제·이름 변경 없음. inbox 브랜치는 건드리지 않음.
1. PR 검토: `python3 -m unittest tests.test_system` (18개) 통과 확인.
2. 08:00 작업 호환성 확인(대표/제작팀): 현재 08:00 프롬프트가 읽는 경로가 inbox 브랜치의 `clips/<날짜>/<에피소드>/scene-NN.mp4` + `manifest.json`과 맞는지. 다르면 08:00 프롬프트의 읽기 경로만 변경(최소 변경).
3. croco-control: 대표가 GitHub ruleset 설정(docs/permissions.md) 후 approvals/budget.json 직접 커밋.
4. 병합 후 첫 실행은 `python3 -m croco.generate --date <내일>` (dry-run, 비용 0)으로 APPROVAL/견적 확인.
5. 문제 시 되돌리기: 병합 PR revert 한 번으로 복구(다른 파일 영향 없음).

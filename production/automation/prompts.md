# 작업 프롬프트 초안 (예약 작업에 붙여 넣기 전 대표 확인용)
## 17:00 마케팅
croco-media를 clone. production/style-guide.md와 episode-template.md를 읽고, 최신 글로벌 키즈 Shorts 트렌드를 조사해
내일 날짜의 서로 다른 에피소드 2편을 briefings/episodes/에 PLANNED JSON으로 작성. 기존 에피소드와 topic_key 중복 금지,
저작권·브랜드·캐릭터 모방 금지. `python3 -m croco.plan_check <내일>`가 OK일 때만 main에 push. 결과를 요약 보고.
## 20:00 V2 생성
croco-media(main)를 clone, `python3 -m croco.generate --date <내일> --live` 실행. 승인 기록이 없거나 BLOCKED이면 아무것도 하지 말고 보고만.
어떤 경우에도 NEEDS_REVIEW/GENERATING 에피소드를 재생성하지 말 것. 출력 요약을 보고.
## 08:00 제작·게시
GENERATED 에피소드만 처리. inbox 브랜치 clips/<날짜>/<id>/manifest.json의 SHA256을 검증 → 편집·효과음 →
영상·오디오 품질, 저작권, 아동 적합성 체크리스트 → publish_guard.claim_edit/mark_qa/claim_publish 순서로 상태 기록 →
통과 시에만 Metricool로 YouTube Shorts 공개 예약 후 record_published. 실패·애매하면 QA_FAILED로 두고 게시 금지, 오류 보고.

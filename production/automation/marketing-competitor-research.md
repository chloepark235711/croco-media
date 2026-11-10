# 마케팅팀 경쟁 채널 조사 (17:00 부서 회의 통합안)

상태: **준비됨 · 운영 미반영** (브랜치 `feature/marketing-competitor-research`). 새 예약 작업 없음. 기존 17:00 회의 안의 한 단계로 들어갑니다.

## 흐름
```
17:00 부서 회의 (기존 루틴, 시각 변경 없음)
 ├ 1. YouTube Analytics (기존, Metricool)
 ├ 2. 트렌드 연구 (기존, WebSearch)
 ├ 2b. 경쟁 채널 조사 ← 신규: python3 -m croco.competitors run  (YouTube Data API v3, 읽기 전용)
 │     → briefings/<today>.md "### 경쟁 채널 조사" 섹션
 ├ 3. 마케팅 제안 (아이디어 3+) ← 2b 근거 인용 필수
 ├ 4. 부서 토론 → 추천 순위
 ├ 8. V2 export  pipeline/v2-episodes/<id>.json  (제작 실제 입력, 변경 없음)
 └ 9. briefings/<D>-marketing-order.md            (08:00 제작팀·20:00 V2 근거 문서, 변경 없음)
18:50 CEO 브리핑(비서실)은 briefings/<today>.md를 그대로 읽음 → 별도 변경 없음
```

## 수집 항목 (공개 API 값만)
| 항목 | 출처 |
|---|---|
| 최근 7일·30일 업로드 수 | uploads 재생목록 (최근 50편 기준, 50편 모두 30일 이내면 `50+`) |
| 영상별 제목·게시일·길이 | videos.list snippet / contentDetails |
| 조회수·좋아요(공개 시) | videos.list statistics (비공개면 "비공개") |
| 공개 구독자 수 | channels.list (숨김이면 "비공개", 0으로 쓰지 않음) |
| 구독자 변화 | **이전 날짜에 저장한 공개값이 있을 때만** (같은 날 값은 기준 아님, 공개값은 반올림됨) |
| 조회수 대비 좋아요 비율 | likes / views |
| 최근 영상 간 성과 차이 | 30일 조회수 중앙값·최대·최소, 최대/중앙 배수 |
| 주제·스토리 형식 | 영상 **제목** 키워드 자동 분류 (설명란 상투 문구 제외) |
| 시청 지속률·클릭률·구독 전환율 | **API 미제공 → 수집·추정하지 않음** |

## 채널 선정 (마케팅팀 자율, 7일마다 재평가)
- 탐색 범위 6개: 글로벌 키즈 애니메이션 / 동물 캐릭터 Shorts / 어린이 교육용 애니메이션 / 짧은 스토리 가족 친화 / 성장 중인 중소형 / 대형 키즈 브랜드(핸들 조회).
- 점수 100 = 콘텐츠 유사성 25 + 시청 대상(아동용 표시 비율 × 영어 적합) 25 + 최근 업로드 활동 25 + 공개 영상 성과 25 (+ 검색 노출 가산 최대 5).
- 후보 10개 → 추적 5개 (가능하면 중소형 2개 이상·대형 브랜드 1개 이상 포함). Croco 자체 채널은 제외.
- 재평가 결과(추가·제외)는 보고서에 표시. 근거는 채널마다 4개 항목 점수와 원값으로 기록.

## 쿼터 (공식: developers.google.com/youtube/v3/determine_quota_cost, 2026-11-03 갱신본 확인)
| 메서드 | 공식 비용 | 비고 |
|---|---|---|
| channels.list / playlistItems.list / videos.list | 1 unit | 일반 할당 10,000 units/일 |
| search.list | 1 unit | **별도 버킷 100회/일** |
| 실패한 요청 | 최소 1 unit | 장부에 실패도 기록 |
- 리셋: 태평양시(PT) 자정. 내부 상한(대표 지시 2026-11-09): **500 units/일**, 보조 상한 search 20회/일 (`CROCO_YT_DAILY_CAP`, `CROCO_YT_SEARCH_CAP`).
- 예상 사용량: 평일 약 13 units(search 1회) · 재평가일 약 70 units(search 6회). 캐시(search·channels 20시간, 영상 6시간)로 같은 요청은 0 unit.
- 모든 호출은 `state.json`의 `ledger`에 시각·엔드포인트·비용·캐시 여부·성공 여부로 남습니다.

## 키 보안
- 키는 환경변수 `YOUTUBE_API_KEY` 또는 `CROCO_YOUTUBE_ENV` 파일(로컬 기본값 `~/.config/croco/youtube.env`)에서만 읽음.
- 요청 헤더 `X-Goog-Api-Key`로만 전송(URL·로그에 없음). 오류 메시지의 키 문자열은 `[REDACTED]`로 바꿈.
- 상태·캐시·보고서·이 저장소에는 키를 쓰지 않음 (테스트로 검증).

## 상태 저장 위치
클라우드 실행은 매번 새 환경이므로 상태 파일을 Claude 프로젝트 `marketing/competitors/state.json`에 보관합니다. 실행 전에 읽고, 실행 후에 저장합니다. 이 파일에는 선정 목록, 구독자 스냅샷, 쿼터 장부, 캐시가 들어 있습니다. 공개 저장소에는 저장하지 않습니다.

## 17:00 회의 프롬프트 삽입문 (승인 후 적용 — 현재 미적용)
기존 2번(트렌드 연구) 다음, 3번 앞에 아래 단락을 넣고, 3번·4번에 표시한 한 줄씩을 덧붙입니다. 실행 시각, 다른 단계, 다른 예약 작업은 바꾸지 않습니다.

> 2b. 마케팅부 — 경쟁 채널 조사 (YouTube Data API v3, read-only, max ~5 minutes): Read the Claude project file marketing/competitors/state.json if it exists and save it to $STATE/state.json. In a read-only clone of croco-media main, run `python3 -m croco.competitors run --state $STATE --out $OUT`. Never print, echo or save the API key; it comes only from the environment variable YOUTUBE_API_KEY. If the command prints "BLOCKED", or the quota cap is reached, write "경쟁 채널 조사 BLOCKED: <reason>" and continue with the rest of the meeting. Then save $STATE/state.json back to marketing/competitors/state.json, and paste $OUT/report.md into the briefing under "### 경쟁 채널 조사". Use only the numbers in that report. Retention, CTR and subscriber conversion of other channels are not available, so never estimate them. Never copy competitors' characters, songs, lyrics, stories, titles or designs, and never put competitor names in Croco titles, descriptions, tags or prompts.
>
> (3번에 추가) Every idea must cite at least one row of "### 경쟁 채널 조사" (a TOP 5 video or a trend) as evidence and explain how Croco makes it original, then give: 오늘의 글로벌 트렌드 TOP 3 요약 → 아이디어 3개 → 첫 3초 후킹·스토리 구조 → 교육적 가치·브랜드 적합성 → 제작 난이도·예상 비용(추정) → 찬성·반대.
>
> (4번에 추가) End with "다음 영상 제작 추천 순위" (1–3위, each with the reason and the evidence row it uses).

## 운영 반영에 필요한 승인 (대표)
1. **클라우드 환경 비밀값:** 17:00 루틴 환경에 `YOUTUBE_API_KEY`를 Network secret으로 추가하는 것. 새 인증 권한을 주는 일이라 승인이 필요합니다.
2. **네트워크 허용:** 클라우드 환경에서 `www.googleapis.com`에 접속할 수 있어야 합니다.
3. **17:00 루틴 프롬프트 수정:** 위 삽입문을 기존 예약 작업에 넣는 것. 기존 예약 작업 변경이라 승인이 필요합니다.
4. **main 병합:** 이 브랜치의 PR을 검토하고 병합하는 것. 17:00 회의는 main을 읽기 전용으로 클론합니다.

# Richgo 시나리오 자동화 V2 구현 계획

> For Hermes: 이 문서는 현재 코드베이스 기준으로 리치고TV용 시나리오 자동화 제품을 재설계한 실행 문서다.

## 2026-04-18 구현 현황 업데이트

### 현재 완료된 범위
- 리서치 세션 생성/확장/복원
  - URL 기반 / 카테고리 기반 시작
  - 기사 / 유튜브 선택 상태 저장
- 주제 추천 고도화
  - 리치고 전용 프롬프트 적용
- 시나리오 워크스페이스 구축
  - `hook_30s`, `bridge_3min`, `body_sections`, `action_takeaways`
  - session_id 기반 저장 / 복원
  - `/workspace/[session_id]` 전용 페이지 추가
- 워크스페이스 후속 액션 연결 완료
  - 검수: `POST /scenarios/workspace/{session_id}/review`
  - 검수 기반 재생성: `POST /scenarios/workspace/{session_id}/regenerate`
  - 나레이션: `POST /scenarios/workspace/{session_id}/narrate`
  - 자막: `POST /scenarios/workspace/{session_id}/subtitles`
  - 썸네일: `POST /scenarios/workspace/{session_id}/thumbnail`
- 각 결과물은 모두 workspace snapshot에 저장되고 재접속 시 다시 확인 가능

### 아직 안 한 것
- 업로드 메타 생성 워크스페이스 연결
- 최종 패키지 뷰
- 실제 자동 업로드

### 현재 DB 상태
- 운영용 Supabase는 아직 연결하지 않음
- 현재는 로컬 SQLite 사용 중
- 실제 기본값: `sqlite:///{DATA_DIR}/youtube.db`
- 구조는 Postgres/Supabase로 나중에 전환하기 쉽게 유지

### 직접 확인용 로컬 주소
- 웹 메인: http://localhost:3737
- API 헬스체크: http://127.0.0.1:8787/health
- 워크스페이스: `http://localhost:3737/workspace/{session_id}`
  - session_id는 메인 화면에서 시나리오 생성 후 진입 가능

### 이번 단계에서 확정한 제품 범위
- 자동 업로드는 아직 붙이지 않는다
- 지금 단계 목표는 "영상 업로드 직전까지 제작 워크스페이스 완성"이다

목표: 최신 경제/부동산/AI 이슈를 빠르게 포착하고, URL 기반 리서치 또는 카테고리 기반 탐색에서 시작해 기사/유튜브 근거를 수집한 뒤 10~15분급 시나리오를 안정적으로 생성하는 시스템으로 고도화한다.

아키텍처 요약:
- 입력 모드 2개: URL 기반 / 카테고리 기반
- 리서치 엔진 3개: 기사 탐색 / 관련 기사 확장 / 유튜브 벤치마크 검색
- 시나리오 엔진 1개: 30초/3분 후킹 강화형 리치고 전용 생성기
- 상태 저장 2개: Supabase DB + 서버 API
- 프론트는 페이지 내부 세션 상태가 아니라 DB 기반 워크스페이스 조회형으로 전환

기술 스택:
- Backend: FastAPI + SQLModel 유지, DB만 Supabase(Postgres) 우선
- Frontend: Next.js App Router 유지
- Search/Data: Naver News API + Google News RSS + YouTube Data API + URL extractor
- DB: Supabase Postgres

---

## 1. 현재 코드베이스 진단

### 이미 있는 것
- `/trends` API 있음
  - Naver 뉴스 / Google News RSS / YouTube 검색 / 일부 커뮤니티 수집 가능
- `/topics`, `/scenarios`, `/reviews`, `/pipeline` API 있음
- SQLModel 기반 `PipelineRun`, `TopicRecord`, `ScenarioRecord` 등 기본 테이블 있음
- 프론트 메인 대시보드에서 트렌드 → 토픽 → 시나리오 흐름이 연결되어 있음

### 부족한 것
- URL 입력 후 관련 기사/유튜브 추천 기능 없음
- 카테고리 선택 → 기사 선택 → 관련 기사 확장 기능 없음
- 시나리오가 10~15분 완성형 구조로 설계돼 있지 않음
- 30초/3분 후킹 최적화 규칙이 프롬프트에 약함
- scenario UI가 독립 컨테이너가 아니라 흐름상 우측 섹션에 붙는 형태
- 상태 저장이 `sessionStorage` 기반이라 새로고침/메뉴 이동 시 깨질 수 있음
- DB는 SQLite 기본, 파일 저장도 많이 섞여 있음
- Supabase 우선 구조 미구현

---

## 2. 제품 요구사항 해석

사용자 의도:
- 최신 어제/오늘의 큰 경제, 부동산, AI 이슈를 매우 빠르게 잡아 영상화하고 싶음
- 단순 요약이 아니라 조회수 잘 나오는 영상 구조까지 자동화하고 싶음
- 기사/유튜브 리서치가 시나리오 생성 이전에 충분히 되어야 함
- 앱을 새로고침하거나 메뉴를 이동해도 상태가 남아 있어야 함

즉 제품의 본체는 “시나리오 생성기”가 아니라 아래 흐름이다:
1. 이슈 발견
2. 근거 수집
3. 관련 기사/유튜브 맥락 확장
4. 조회수 높은 포맷 추출
5. 리치고 톤으로 재구성
6. 10~15분 분량 시나리오 생성

---

## 3. 새 입력 모드 설계

### 모드 A: URL 입력 기반
입력:
- 사용자가 뉴스 URL 또는 유튜브 URL 입력

시스템 동작:
1. URL 본문/메타 추출
2. 핵심 키워드 5~10개 추출
3. 관련 기사 10개 추천
4. 관련 유튜브 10개 추천 (조회수/최근성/채널 적합성 반영)
5. 기사/영상 선택 후 시나리오 생성으로 연결

필수 API 제안:
- `POST /research/from-url`
- body:
  ```json
  {
    "url": "https://...",
    "category_hint": "realestate | economy | ai | auto"
  }
  ```

응답 예시:
```json
{
  "source": {
    "type": "article",
    "title": "...",
    "summary": "...",
    "keywords": ["금리", "서울 아파트", "대출"]
  },
  "related_articles": [...],
  "related_videos": [...]
}
```

### 모드 B: 카테고리 선택 기반
입력:
- 카테고리: 부동산 / 경제 / AI

시스템 동작:
1. 최신 기사 20개 노출
2. 사용자가 기사 체크
3. 체크한 기사와 관련 기사 추가 10~20개 추천
4. 관련 주제의 조회수 좋은 유튜브 추천
5. 선택 결과를 근거로 토픽 후보 생성
6. 시나리오 생성 연결

필수 API 제안:
- `GET /research/categories/{category}/articles`
- `POST /research/expand-articles`
- `POST /research/related-videos`

---

## 4. 새 백엔드 컴포넌트 설계

### 4-1. ResearchSession 테이블
파일 저장 대신 DB 중심으로 가기 위해 세션 개념 추가.

새 테이블:
- `ResearchSession`
  - id
  - mode (`url`, `category`)
  - category
  - source_url
  - source_title
  - source_summary
  - source_keywords (JSON)
  - selected_article_ids (JSON)
  - selected_video_ids (JSON)
  - created_at / updated_at

### 4-2. ArticleRecord 테이블
- id
- session_id
- title
- source
- url
- published_at
- summary
- keywords (JSON)
- related_score
- selected

### 4-3. VideoReferenceRecord 테이블
- id
- session_id
- youtube_video_id
- title
- channel
- url
- views
- published_at
- relevance_score
- selected

### 4-4. ScenarioWorkspace 테이블
시나리오 결과를 별도 독립 저장
- id
- session_id
- selected_topic
- target_duration_min
- target_duration_max
- hook_30s
- bridge_3min
- body_outline (JSON)
- full_script_markdown
- title_candidates (JSON)
- thumbnail_candidates (JSON)
- references_snapshot (JSON)
- status
- created_at / updated_at

---

## 5. Supabase 우선 구조

### 현재 상태
- `settings.database_url` 기본값이 sqlite
- SQLModel 자체는 Postgres로 쉽게 전환 가능

### 변경 원칙
- 기본 DB를 Supabase Postgres URL로 받는다
- SQLite는 개발용 fallback만 유지

변경 포인트:
- `.env`
  - `DATABASE_URL=postgresql+psycopg://...`
- `app/core/config.py`
  - database_url 기본값은 sqlite 유지하되 README/배포 설정은 Supabase 우선으로 변경
- `app/core/db.py`
  - Postgres connection에서 pool_pre_ping, pool_recycle 설정 추가 권장

추가 추천:
- Supabase Storage는 썸네일/자막/렌더 결과물 저장용으로만 사용
- 본문/시나리오/기사 메타는 DB 테이블에 저장

---

## 6. 프론트 상태 저장 전략

### 현재 문제
- `apps/web/app/store.ts` 에서 `sessionStorage` 사용
- 새로고침 시 일부만 유지되고, 메뉴 이동하면 재조회/상태 유실

### 바꿔야 하는 방향
- 브라우저 세션 저장소 중심 → 서버 저장소 중심
- 프론트는 항상 `workspaceId` 또는 `sessionId`만 라우트/쿼리로 들고 다님

### 제안
- 메인 플로우를 `/workspace/[id]` 기반으로 변경
- 페이지별 컴포넌트는 DB에서 읽기
- 필요시 `localStorage`에는 마지막 workspace id 정도만 저장

### 결과
- 새로고침: 유지됨
- 메뉴 이동: 유지됨
- 다른 디바이스/브라우저: 동일 세션 접근 가능

---

## 7. 시나리오 UI 재설계

### 현재 문제
- 시나리오가 선택 결과 옆에 붙어서 보임
- 사용자가 “우측끝에 나오는 게 아니라 섹션을 따로 컨테이너 구분” 원함

### 제안 레이아웃
1. 상단: 입력 모드 전환 탭
   - URL 기반
   - 카테고리 기반
2. 좌측 컬럼: 기사/유튜브 리서치 선택 패널
3. 중앙 컬럼: 토픽 후보 + 근거 비교
4. 하단 전체 폭 독립 컨테이너: 시나리오 생성 결과
   - Hook 0~30초
   - 30초~3분 확장부
   - 3~10분 본문 전개
   - 10~15분 결론/CTA
5. 별도 컨테이너: 제목 후보 / 썸네일 후보 / 참고 레퍼런스

핵심:
- 시나리오는 “결과 패널”이 아니라 “핵심 작업공간”이어야 함
- width 100% 독립 섹션으로 빼는 게 맞음

---

## 8. 시나리오 생성 규칙 재설계

### 사용자의 요구 반영
- 10~15분 분량
- 제목 설명 형식
- 초기 30초와 3분 집중도 극대화
- 후킹이 강해야 함

### 내가 추천하는 실제 구조
10~15분이 무조건 정답은 아니야.
내 기준에서는 리치고TV 같은 경제/부동산 해설 채널은 아래가 더 맞다:
- 초속보형: 6~9분
- 일반 이슈형: 9~12분
- 깊은 분석형: 12~16분

즉 “항상 10~15분”보다,
- 긴급 이슈는 8~10분으로 더 타이트하게
- 중요 매크로/부동산 구조 변화는 11~14분으로 깊게
가 더 조회수/시청지속시간 균형이 좋을 가능성이 높다.

추천 정책:
- default 목표: 10~12분
- depth_score 높을 때만 13~15분 확장

### 시나리오 섹션 구조
1. `opening_title`
   - 영상 첫 문장 전 화면 텍스트성 설명
2. `hook_30s`
   - 0~30초
   - 지금 안 보면 안 되는 이유
   - 손실 회피 / 오해 반전 / 오늘 판단 포인트
3. `bridge_3min`
   - 30초~3분
   - 사건 요약 + 왜 중요한지 + 누구에게 영향인지
4. `body_sections`
   - 3~10분
   - 원인
   - 시장 영향
   - 부동산/경제 연결
   - 데이터/사례
   - 반론/예외
5. `action_takeaways`
   - 지금 시청자가 체크할 포인트
6. `closing_cta`
   - 지역/자산/생각 댓글 유도

---

## 9. 새 시나리오 프롬프트 제안

### system 역할
- 리치고TV 전용 해설 작가
- 과장 금지
- 속보형 뉴스 채널이 아니라 “해석과 판단” 중심
- 첫 30초와 첫 3분에서 이탈률 방어가 최우선

### prompt 핵심 규칙
- 제목 설명형으로 시작
- 0~30초: 손실회피/기회상실/반전정보 훅 중 최소 2개 사용
- 30초~3분: 사건 요약 + 시청자 영향 + 오늘의 판단 질문 제시
- 3분 이후: 데이터·비교·사례·반론 구조
- 영상 길이는 목표 시간을 받아서 조절
- 단락마다 “왜 지금 이 얘기를 들어야 하는가”가 살아 있어야 함

### 권장 출력 스키마
```json
{
  "opening_title": "...",
  "hook_30s": "...",
  "bridge_3min": "...",
  "body_sections": [
    {"heading": "핵심 원인", "script": "..."},
    {"heading": "시장 영향", "script": "..."},
    {"heading": "부동산 연결", "script": "..."},
    {"heading": "예외와 반론", "script": "..."}
  ],
  "action_takeaways": ["...", "...", "..."],
  "closing_cta": "...",
  "title_candidates": ["..."],
  "thumbnail_candidates": ["..."],
  "estimated_duration_min": 11
}
```

### 프롬프트 초안
```md
너는 리치고TV의 수석 시나리오 작가다.
이번 영상은 최신 이슈를 빠르게 해석해 시청자가 '지금 무엇을 판단해야 하는지' 알게 하는 것이 목표다.

반드시 지켜라:
1. 첫 30초는 절대 약하면 안 된다.
2. 첫 3분 안에 사건 요약, 시청자 영향, 오늘의 판단 포인트가 모두 나와야 한다.
3. 경제/부동산/AI 이슈라도 결국 '내 삶과 자산에 어떤 영향이 있는가'로 연결해야 한다.
4. 과장, 공포 조장, 확인 안 된 루머 금지.
5. 말투는 차분하지만 집중도는 높아야 한다.

영상 목표 길이: {{target_duration}}
영상 형식: 제목 설명형 + 해설형
참고 기사: {{selected_articles_json}}
참고 유튜브: {{selected_videos_json}}
핵심 주제: {{topic}}

출력은 JSON만.
```

---

## 10. URL 관련 기사/유튜브 찾기 방식 추천

### URL이 뉴스일 때
1. 기사 제목/본문에서 키워드 추출
2. 같은 키워드로 최근 기사 재검색
3. 기사 source 다양성 확보 (같은 언론사만 10개 금지)
4. 같은 키워드로 YouTube 검색 + 조회수/최근성 정렬

### URL이 유튜브일 때
1. 영상 제목/설명/채널/업로드 시점 추출
2. 동일 키워드 기반 기사 검색
3. 경쟁 유튜브 검색
4. 관련 주제의 상위 조회수 영상 추출

추천 점수식:
- article relevance = keyword_overlap + recency + source_diversity
- video relevance = keyword_overlap + log(views) + freshness + richgo_fit

---

## 11. 구현 우선순위

### Phase 1 — 제품 본체부터
1. ResearchSession / ArticleRecord / VideoReferenceRecord / ScenarioWorkspace 테이블 추가
2. Supabase DB 연결 전환
3. URL 기반 리서치 API 추가
4. 카테고리 기반 기사 목록 + 관련 기사 확장 API 추가
5. 관련 유튜브 추천 API 추가

### Phase 2 — 시나리오 품질
6. ScenarioOutput 스키마 확장 (`hook_30s`, `bridge_3min`, `body_sections`, `estimated_duration_min`)
7. `prompts/scenario_generate.md` 전면 개편
8. 시나리오 전용 독립 컨테이너 UI 구현

### Phase 3 — 상태 유지
9. `sessionStorage` 제거 또는 보조화
10. `/workspace/[id]` 기반 라우팅
11. 메뉴 이동/새로고침 후 DB 재복원 구현

### Phase 4 — 고급화
12. 기사/영상 선택 근거 표시
13. “왜 이 주제를 선택했는지” explainability 패널
14. 성과 데이터 기반 길이 추천 엔진

---

## 12. 내가 추가로 추천하는 더 좋은 방법

### 추천 1: “속보 시나리오 모드” 추가
항상 같은 길이로 만들지 말고:
- 속보 모드: 6~9분
- 일반 분석 모드: 10~12분
- 딥다이브 모드: 13~15분

### 추천 2: 기사 선택보다 “핵심 주장” 선택
기사 10개를 다 읽는 것보다, 시스템이 먼저 주장 포인트를 뽑아주면 더 빠르다.
예:
- 금리 인하 기대감 확대
- 서울 핵심지 거래 반등
- 전세 시장 불안 재점화
이런 주장 체크 방식이 더 생산적일 수 있음.

### 추천 3: 유튜브 벤치마크는 제목/조회수만 보지 말고 구조도 저장
조회수 좋은 유튜브는 반드시 아래를 저장해야 함:
- 제목
- 첫 문장
- 썸네일 문구
- 길이
- 업로드 시점
그래야 시나리오 품질이 확 올라감.

### 추천 4: “오늘 바로 찍을 수 있는가” 점수 추가
지금 6축 점수 외에 하나 더 넣는 게 좋다:
- production_readiness (바로 제작 가능성)
이게 높아야 실제 실행 속도가 빨라짐.

---

## 13. 결론

짱보스 의도에 가장 맞는 방향은 이거야:
- 단순 트렌드 스캔 도구가 아니라
- 최신 이슈를 빠르게 영상화하는 “리서치-시나리오 워크스페이스”로 바꾸는 것

핵심 결정:
- URL 입력 기반 리서치 추가
- 카테고리 → 기사 선택 → 관련 기사/유튜브 확장 흐름 추가
- 시나리오는 10~12분 기본, 필요 시 13~15분 확장
- 30초/3분 후킹 강화형 프롬프트로 전면 개편
- 새로고침/메뉴 이동 유지 위해 DB 중심 상태 저장
- 파일 저장 중심에서 Supabase DB 중심으로 전환

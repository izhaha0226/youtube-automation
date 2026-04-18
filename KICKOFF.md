# YouTube 자동화 프로젝트 — 개발 착수 프롬프트 (Kickoff)

> 대표님 승인받기 위한 단 1회 문서.
> 승인 후부터는 **자율 실행** 모드로 전환 (AIMTOP-DEV-HARNESS 준수).
> 작성일: 2026-04-17

---

## 1. 이해한 것 (Obsidian 기획 문서 요약)

- **채널**: 리치고 (김기원 대표) — 경제/부동산 해설
- **기본 모델**: gpt-5.4, 백업: claude
- **핵심 파이프라인**:
  `의도 한 줄 → 이슈/트렌드 스캔 → 주제선정(6축 점수) → 시나리오 → 검수 → 나레이션 → EN/JA/ZH 자막 → 썸네일 → 업로드 메타 → 자동 배포 → 성과 추적 → 자동 최적화`
- **운영 모드**: 자율 실행. 최종 결과만 사람이 확인.
- **저장 순서 규칙**: Obsidian Vault 먼저 → 확인 → Workspace 동기화
- **IO 규격**: 모듈별 JSON 입출력 스키마가 이미 문서화되어 있음 (주제선정/시나리오/검수/썸네일/UI/동기화)

## 2. 아키텍처 (AIMTOP 하네스 표준 준수)

```
youtube-automation/
├── apps/
│   ├── api/                 # FastAPI 백엔드 (Railway 배포)
│   │   ├── main.py
│   │   ├── routes/          # /topics /scenarios /reviews /narrations /subtitles /thumbnails /uploads /performance
│   │   ├── core/            # config, db, llm provider, logging
│   │   └── modules/         # 각 기능 모듈 (topic_selector, scenario_gen, reviewer, narration, subtitle, thumbnail, uploader, performance)
│   └── web/                 # Next.js 대시보드 (Vercel 배포)
├── packages/
│   └── schemas/             # Pydantic + zod 공유 IO 스키마
├── configs/
│   ├── config.yaml          # 프로젝트/채널/공유링크
│   ├── channel_richgo.yaml  # 리치고 톤/철학/프로필
│   └── scoring.yaml         # 주제선정 6축 점수 규칙
├── prompts/                 # gpt-5.4용 프롬프트 템플릿 (주제/시나리오/검수/나레이션/번역/썸네일문구)
├── data/                    # 산출물 (topic/scenario/narration/srt/thumb/meta/package)
├── scripts/
│   ├── deploy-check.sh      # AIMTOP 필수 검증
│   ├── run_pipeline.py      # E2E CLI 자율실행 진입점
│   └── sync_obsidian.py     # Obsidian↔Workspace 동기화
├── AGENTS.md                # AIMTOP 표준 컨텍스트
├── .env.example
└── README.md
```

## 3. 기술 스택 (AIMTOP 표준)

| 레이어 | 선택 | 근거 |
|---|---|---|
| 백엔드 | Python 3.12 + FastAPI | AIMTOP 표준. LLM/유튜브/TTS 생태계 Python이 최적 |
| DB | Postgres (Neon) + SQLModel | AIMTOP 표준. 로컬은 SQLite fallback |
| LLM | gpt-5.4 기본 / claude 백업 | 문서 규정. provider 어댑터로 교체 용이 |
| 프론트 | Next.js 16 + TypeScript (Vercel) | AIMTOP 표준 |
| 작업큐 | 내부 asyncio 큐 + Redis 없을 시 파일 락 | 단순/확장 모두 대응 |
| 배포 | Railway(API) + Vercel(Web) | AIMTOP 표준 |
| 로깅 | structlog + 파일 + 콘솔 |  |

## 4. 승인이 꼭 필요한 결정 (이번 1회만)

> **아래 5개만 확정 부탁드립니다. 이후는 전부 자율 실행합니다.**

### ① TTS (나레이션) 엔진
- **A. ElevenLabs Multilingual v2** — 퀄리티 최고, 한국어 자연스러움 최상, 비용 높음 ($5~22/월 + usage)
- **B. Azure Neural TTS** — 한국어 강함, 적정 비용, 안정성 높음 ✅ **기본 추천**
- **C. OpenAI TTS** — 저렴하지만 한국어 톤 약함

### ② YouTube 자동 업로드 방식
- **A. 공식 YouTube Data API v3 + OAuth 2.0** — 완전 자동, 최초 1회 OAuth 필요 ✅ **기본 추천**
- **B. 업로드 패키지만 생성 → 수동 업로드** — 심플, 안전, 자율실행 아님

### ③ 썸네일 이미지 생성
- **A. Fal.ai (문서 명시)** ✅ **기본 추천 — 문서 규정대로**
- **B. Replicate/Stable Diffusion** — 대안

### ④ 성과 추적 + 자동 최적화 범위 (v1)
- **A. 수집만** — 조회수/CTR/체류시간 대시보드 표시
- **B. 수집 + 인사이트 리포트** — 주간 성과 요약 + 개선 제안 ✅ **기본 추천**
- **C. 수집 + 피드백 루프** — 분석 결과로 다음 주제선정 가중치 자동 조정 (v2로 분리 제안)

### ⑤ Obsidian Vault 쓰기
- 경로: `/Users/yosiki/Documents/Obsidian Vault/wiki/YouTube 자동화프로젝트/`
- **파이프라인 산출물을 Obsidian에 먼저 저장 → Workspace 복제** 규칙 적용 OK?
- share link: https://share.note.sx/qynhdluo (문서 규정대로 반영)

## 5. 승인 후 자율 실행 순서 (16개 태스크)

1. 스캐폴드 + AGENTS.md + deploy-check.sh
2. 설정/모델 프로바이더 레이어 (gpt-5.4 / claude 백업)
3. 데이터 스키마 + DB
4. 트렌드/이슈스캔 모듈
5. 주제선정 (6축 점수화, 24점↑ 적극추천 규칙 반영)
6. 시나리오 생성 (훅/본문3/경제연결/사례/결론/CTA/제목5/썸네일3)
7. 검수 (사실/과장/SEO/톤)
8. 나레이션 + EN/JA/ZH 자막 (SRT + JSON meta)
9. 썸네일 (Fal.ai + 프로필 오버레이)
10. 업로드 메타 + 배포 패키지
11. YouTube 자동 업로드
12. 성과 추적 + 자동 최적화
13. Next.js 대시보드
14. Obsidian↔Workspace 동기화
15. E2E 자율실행 파이프라인 (CLI `run_pipeline.py` 한 줄로 전체 실행)
16. QA + deploy-check 통과 후 Railway/Vercel 배포

## 6. 자율 실행 중 보고 방식

- **중간 코드/에러 로그 노출 안 함** (대표님 규칙)
- 각 태스크 **완료 시에만** 짧게 보고 (한 줄)
- 근본 판단이 필요한 경우만 중단 후 질문 (예: 새 API 키 필요, 유료 서비스 결제)

## 7. 확인 포인트 (한 줄 답변으로 충분)

> **"①~⑤ 전부 기본 추천(Azure / OAuth / Fal.ai / B 인사이트 리포트 / Obsidian 동기화 ON)으로 가자" 라고 답하시면 즉시 착수합니다.**
> 변경하실 항목만 번호로 집어주세요.

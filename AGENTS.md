# AGENTS.md — YouTube Automation

## 프로젝트
리치고 채널 자동화. 의도 한 줄 → 주제선정 → 시나리오 → 검수 → 나레이션 → EN/JA/ZH 자막 → 썸네일 → 업로드 메타 → YouTube 자동 배포 → 성과 추적 → 자동 최적화.

## 기술 스택
- 백엔드: Python 3.12, FastAPI, SQLModel, Pydantic v2, structlog, httpx, tenacity
- 프론트: Next.js 16 + TypeScript + Tailwind + shadcn/ui
- DB: Postgres(Neon) / 로컬 SQLite fallback
- LLM: gpt-5.4 (기본), claude (백업)
- TTS: Azure Neural
- 이미지: Fal.ai
- 배포: Railway(API) + Vercel(Web)

## 포트
- API: 8787
- Web: 3737

## 디렉터리
```
apps/api        FastAPI 백엔드
apps/web        Next.js 대시보드
packages/schemas  공유 IO 스키마
configs         config.yaml / channel_richgo.yaml / scoring.yaml
prompts         gpt-5.4 프롬프트 템플릿
data            파이프라인 산출물
scripts         CLI 진입점, deploy-check
```

## 배포
```bash
# API → Railway
cd apps/api && railway up

# Web → Vercel
cd apps/web && vercel --prod
```

## 절대 금지
- Anthropic/OpenAI API 키를 코드에 하드코딩
- 더미/가짜 데이터 DB 삽입 (대표님 명시 지시 없이)
- 임시 파일 커밋 (temp_*, debug_*, fix_*, migrate_*)
- .env 커밋
- 로컬 테스트/`deploy-check.sh` 미통과 상태 배포
- Obsidian Vault 직접 덮어쓰기 전 백업 없음
- Claude API 직접 호출 금지 — Claude CLI(`claude --print`) 또는 provider 어댑터만

## 배포 전 체크 (scripts/deploy-check.sh)
1. `python -c "from app.main import app"` import 통과
2. `python -c "from app.core.config import settings"` 설정 로딩 확인
3. `cd apps/web && npm run build` 성공
4. `cd apps/web && npx tsc --noEmit` 타입 통과
5. `curl -sf http://localhost:8787/health` 200 응답

## DB 규칙
- ORM(SQLModel)만 사용, 직접 SQL 금지
- 마이그레이션은 alembic

## 데이터 저장 순서
1. Obsidian Vault에 먼저 저장
2. 파일 존재 확인
3. Workspace (data/) 동기화

## 운영 모드
자율 실행. 최종 결과만 사람이 확인.

## LLM 호출 규칙
- 기본 모델: `settings.default_model` = gpt-5.4
- 백업: `settings.backup_model` = claude
- provider 어댑터 `app.core.llm.LLMProvider`만 통해 호출

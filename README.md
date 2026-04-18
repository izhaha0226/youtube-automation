# youtube-automation

리치고 채널 자동화 파이프라인. gpt-5.4 기본.

## 빠른 시작

```bash
# 1. 환경변수
cp .env.example .env
# .env 채우기

# 2. 백엔드
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --port 8787 --reload

# 3. 프론트
cd apps/web
npm install
npm run dev

# 4. E2E 자율실행 (한 줄)
python scripts/run_pipeline.py --intent "금리 변화가 집값에 주는 영향" --auto
```

## 구조
- `apps/api` FastAPI 백엔드
- `apps/web` Next.js 대시보드
- `packages/schemas` 공유 IO 스키마
- `configs` 설정 파일
- `prompts` gpt-5.4 프롬프트
- `data` 파이프라인 산출물

세부 규칙은 `AGENTS.md`.

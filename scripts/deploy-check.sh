#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[1/5] API import check"
(cd apps/api && python3 -c "from app.main import app")

echo "[2/5] settings load"
(cd apps/api && python3 -c "from app.core.config import settings; print('model=', settings.default_model)")

echo "[3/5] web typecheck"
(cd apps/web && npx --yes tsc --noEmit)

echo "[4/5] web build"
(cd apps/web && npm run build)

echo "[5/5] hardcoded secrets scan"
if grep -rn "sk-[A-Za-z0-9]\{20,\}\|api_key\s*=\s*['\"][A-Za-z0-9]" --include="*.py" --include="*.ts" --include="*.tsx" apps packages scripts 2>/dev/null | grep -v ".env.example"; then
  echo "BLOCK: hardcoded secrets"
  exit 1
fi

echo "deploy-check OK"

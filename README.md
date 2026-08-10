# crecity

브랜드와 인플루언서/UGC 크리에이터를 연결하는 셀프서브 마켓플레이스 (Collabstr 한국판).

- 요구사항 정본: `_docs/collabstr-analysis.md`
- 백엔드: `crecity/` — Python 3.13 · FastAPI · 헥사고날/클린 + 허브-스포크 스타 토폴로지
- 프론트엔드: `www/` — Next.js 16 · TypeScript · Tailwind 4
- 개발 규칙: `CLAUDE.md` (루트) → 영역별 `_docs/CLAUDE.md`

## 시작하기

```bash
# 인프라 (postgres:5433 · redis:6380)
docker compose up -d

# 백엔드 — http://127.0.0.1:8000 (문서: /docs)
python3.13 -m venv .venv && .venv/bin/pip install -r crecity/requirements.txt
cd crecity && ../.venv/bin/uvicorn main:app --reload

# 프론트엔드 — http://localhost:3000
cd www && pnpm install && pnpm run dev
```

## 검증

```bash
PYTHONPATH=crecity:crecity/apps .venv/bin/python -m pytest crecity/apps -q
cd crecity && PYTHONPATH=apps ../.venv/bin/lint-imports --config .importlinter
cd www && pnpm run typecheck
```

git 훅(pre-commit=lint-imports, pre-push=pytest)이 안전망이다. 새 클론에서는 한 번 실행:

```bash
git config core.hooksPath scripts/git-hooks
```
# com.crecity

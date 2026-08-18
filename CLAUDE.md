# CLAUDE.md — 프로젝트 루트

에이전트(Claude Code, Cursor 등)는 코드·설정·명령을 제안·실행하기 전에 본 문서를 먼저 읽고,
프로젝트별 지침과 병합해 해석한다. 구조·컨벤션은 `com.redoceanmap`을 정본 레퍼런스로 따른다.

## 언어 설정

- 항상 한국어로 응답한다.

---

## 프로젝트 개요

**crecity** — 브랜드와 인플루언서/UGC 크리에이터를 연결하는 셀프서브 마켓플레이스(Collabstr 한국판).
요구사항 정본: [[_docs/collabstr-analysis|collabstr 분석 보고서]] (주문 상태머신·수수료·에스크로 정책 포함).

한 저장소에 백엔드·프론트엔드가 함께 있다.

| 영역 | 스택 | 위치 |
| --- | --- | --- |
| 백엔드 | Python 3.13 · FastAPI · SQLAlchemy 2.0(asyncio) · Pydantic 2 | `crecity/` |
| 프론트엔드 | Next.js 16 · React 19 · TypeScript 5 · Tailwind 4 · zustand · TanStack Query | `www/` |
| 데이터 | PostgreSQL 17(`:5433`) · Redis 7(`:6380`) | 도커 컴포즈 |

백엔드는 **모듈러 모놀리식**이다. 앱 내부는 헥사고날/클린(`adapter → app → domain`),
앱 사이는 스타 토폴로지(허브 `hub` + 스포크)이며 두 구조는 `crecity/.importlinter`로 강제된다.
프론트엔드는 브라우저 fetch를 `/api/backend` rewrite로만 백엔드에 보낸다.

---

## 하위 CLAUDE.md 링크 (WikiLink)

작업 디렉토리가 아래 영역에 속하면 해당 CLAUDE.md를 **먼저 읽고** 규칙을 적용한다.
각 영역 루트의 `CLAUDE.md`는 `_docs/CLAUDE.md`로의 **심볼릭 링크**다(실내용은 `_docs/`에).

| 영역 | 문서 |
| --- | --- |
| 백엔드 (Python / FastAPI) | [[crecity/_docs/CLAUDE\|crecity CLAUDE]] |
| 앱 경계·트랜잭션 경계 설계 | [[crecity/_docs/BOUNDARIES\|BOUNDARIES]] |
| 프론트엔드 (Next.js) | [[www/_docs/CLAUDE\|www CLAUDE]] |

> 앱은 **스타 토폴로지**(허브 `hub` + 스포크)다. 앱별 문서는 [[crecity/_docs/CLAUDE|crecity CLAUDE]]의
> 앱 표에서 잇는다. 새 앱은 `crecity/apps/<app>/_docs/CLAUDE.md` + 심볼릭 링크
> `<app>/CLAUDE.md → _docs/CLAUDE.md`를 같은 패턴으로 추가한다.

---

## 자동 적용 규칙 — 프론트엔드(www)

`www/` 디렉토리의 React/Next.js 코드(`.tsx` / `.ts`)를 읽거나 작성·수정할 때는
`www/_docs/REACT_RULES.md`를 먼저 읽고 자동 적용한다.

- **핵심 규칙:** 하나의 컴포넌트에 `useState`가 2개 이상이면 묻지 말고 FormData 패턴(폼 제출)
  또는 단일 객체 패턴(실시간 상태)으로 압축한다.
- **예외:** 사용자가 명시적으로 "useState 유지"를 요청한 경우.
- **결과 보고:** 어떤 패턴을 적용했는지 한 줄로 명시한다.

---

## 공통 행동 원칙

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked. No abstractions for single-use code.
- If you write 200 lines and it could be 50, rewrite it.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

- Don't "improve" adjacent code, comments, or formatting.
- Match existing style, even if you'd do it differently.
- Remove imports/variables/functions that YOUR changes made unused.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- For multi-step tasks, state a brief plan with per-step verification.

---

## 명령어

백엔드는 프로젝트 루트 `.venv`(Python 3.13)로 실행한다. 프론트는 pnpm.

```bash
# 인프라 기동 — postgres:5433 · redis:6380 (모두 127.0.0.1 루프백 바인딩)
docker compose up -d

# 백엔드 개발 서버 — http://127.0.0.1:8000
cd crecity && ../.venv/bin/uvicorn main:app --reload

# 백엔드 테스트 전체
PYTHONPATH=crecity:crecity/apps .venv/bin/python -m pytest crecity/apps -q

# import-linter — 아키텍처 계약 5종(클린 아키텍처 · 스포크 상호 독립 ·
#                  프레임워크 격리 · 도메인 순수성 · 허브 격리)
cd crecity && PYTHONPATH=apps ../.venv/bin/lint-imports --config .importlinter

# 프론트엔드 개발 서버 (패키지 매니저는 pnpm — pnpm-lock.yaml이 정본)
cd www && pnpm run dev

# 프론트엔드 타입 체크 (반드시 package.json 스크립트로 — npx tsc 직접 실행 금지)
cd www && pnpm run typecheck
```

- **스모크 회귀**(서버를 띄운 뒤): `.venv/bin/python scripts/smoke.py [--frontend]`
  — 라우터 조립·권한 게이트·응답 필드·DB 정합성을 실제 서버에 대고 확인한다.
  pytest·typecheck가 못 잡는 영역이다(스텁·타입은 실제 응답을 보지 않는다).
- **E2E 화면 회귀**(백엔드+프론트 기동 뒤): `.venv/bin/python scripts/e2e.py`
  — 로그인 상태의 실제 브라우저 렌더를 검증한다(리프레시 토큰 쿠키 주입 → 세션 복원).
  스모크가 못 보는 "화면이 제대로 그려지는가"를 잡는다(리뷰 블러·채팅 스크롤 회귀 포함).
  설치된 Chrome을 쓰며, `--viewport 375`로 모바일 폭 점검.
- **개발용 토큰**(로그인이 필요한 API를 확인할 때):
  `cd crecity && PYTHONPATH=.:apps ../.venv/bin/python scripts/dev_issue_token.py <이메일>`
  (계정 목록은 `--list`). 실제 발급기를 그대로 쓰므로 진짜 토큰과 같다.
  **로컬 DB가 아니면 실행을 거부한다**(`--force`로만 넘긴다).
- 마이그레이션: `cd crecity && PYTHONPATH=apps ../.venv/bin/alembic upgrade head`
  (새 ORM은 `alembic/env.py`에 import 등록 → `revision --autogenerate` → `upgrade head`).

---

## 코딩 컨벤션

| 영역 | 정본 |
| --- | --- |
| 백엔드 | [[crecity/_docs/CLAUDE\|crecity CLAUDE]] |
| 프론트엔드 | [[www/_docs/CLAUDE\|www CLAUDE]] · [[www/_docs/REACT_RULES\|REACT_RULES]] |

- **주석·문서·커밋 메시지는 한국어.** 커밋은 `type(scope): 요약` 형식(예: `fix(auth): …`).
- **백엔드:** I/O-bound는 `async def`, CPU-bound는 `def`. 포트(ABC)와 구현체의 `def`/`async def`를
  일치시킨다. 유스케이스는 어댑터 스키마가 아니라 `app/dtos`를 받는다.
- **백엔드 임계값·상수:** `load_dotenv`·`os.getenv`를 새로 쓰지 않는다 —
  `core/key/secret_manager.py`(스크립트·엔트리포인트) 또는 `core/config.py`(런타임) 경유.
- **프론트엔드:** strict mode 유지, `any` 금지, `interface`보다 `type`,
  백엔드 응답 필드명은 변환하지 않는다.
- 새 라우터는 `GET <prefix>/myself` 자기소개 + 헥사고날 프랙탈 단면을 함께 만든다(백엔드 정본 참고).

---

## 테스트

- 프레임워크: **pytest + pytest-asyncio**(`asyncio_mode = auto` — `@pytest.mark.asyncio` 불필요).
- 테스트 파일: `test_*.py` 패턴, 앱별 `crecity/apps/<app>/tests/` 아래.
- 유스케이스는 **스텁 포트**로 검증한다(mock 프레임워크보다 스텁 구현 선호).
- 구조 위반은 테스트가 아니라 import-linter가 잡는다. 아키텍처를 건드린 변경은 둘 다 돌린다.
- 프론트엔드에는 테스트 러너가 없다 — 검증 수단은 `pnpm run typecheck`뿐이다.

---

## 브랜치 전략

- 원격: `https://github.com/redoceanmap/com.crecity.git`
- `main` — 원격 기본 브랜치. `min` — 작업 브랜치(이 맥). 커밋·push는 사용자가 요청할 때만 한다.

---

## 환경 변수

- `.env` — 실제 값(git 제외). 키를 추가하면 **`.env.example`에도 반드시 등록**한 뒤
  `crecity/core/config.py`에 상수 한 줄을 더한다.
- 필수: `DATABASE_URL`(`core/config.py`가 없으면 기동 거부).
- `.env.auth` — 추후 auth가 토큰을 발급하게 되면 개인키 전용 파일로 쓴다.
  자동 로드되지 않으며 `load_auth_env()`를 명시 호출한 프로세스만 본다.

---

## 주의사항

- **스포크끼리 직접 import 금지.** 교차 협력은 허브(`apps/hub`) 포트 경유. 허브는 스포크를 모른다.
- **DB 포트는 5433/6380.** redoceanmap 백엔드 PC 포워딩(5432/6379)과 충돌 이력이 있어
  비켜 놓았다 — 기본 포트로 되돌리지 말 것.
- **비밀값을 로그·커밋·문서에 남기지 않는다.** `.env*` 파일 내용을 그대로 출력하지 않는다.
- **프론트엔드 브라우저 fetch는 절대 URL을 쓰지 않는다** — `/api/backend` rewrite 경유.
- 볼륨 삭제·`down -v`·스키마 파괴 명령은 사용자 확인 없이 실행하지 않는다.
- GitHub Actions 등 CI는 도입하지 않는다. 대신 **로컬 git 훅이 안전망**이다 —
  pre-commit=`lint-imports`, pre-push=`pytest`(`scripts/git-hooks/`).
  새 클론에서는 `git config core.hooksPath scripts/git-hooks`를 한 번 실행한다.
- **트랜잭션 경계 원칙**: 원자성이 필수인 상태 변경은 같은 스포크(같은 DB 트랜잭션)에 둔다.
  Saga·이벤트 버스는 도입하지 않는다. 상세와 스포크 경계는 [[crecity/_docs/BOUNDARIES|BOUNDARIES]].
- 외부 서비스는 무료 범위만 사용한다.

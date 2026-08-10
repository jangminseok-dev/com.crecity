# CLAUDE.md — 프론트엔드 (www)

공통 원칙 → [[CLAUDE|CLAUDE (루트)]] · React 상태 규칙 → [[www/_docs/REACT_RULES|REACT_RULES]]

Next.js 16(App Router) · React 19 · TypeScript 5 · Tailwind 4 · zustand · TanStack Query.
패키지 매니저는 **pnpm**(`pnpm-lock.yaml`이 정본).

## 규칙

- **브라우저 fetch는 절대 URL 금지** — `/api/backend/:path*` rewrite(next.config.ts) 경유만.
  백엔드 응답 필드명은 변환하지 않는다.
- strict mode 유지, `any` 금지, `interface`보다 `type`.
- `useState` 2개 이상이면 REACT_RULES.md의 FormData 패턴/단일 객체 패턴으로 압축.
- 서버 상태는 TanStack Query, 클라이언트 전역 상태는 zustand. Provider는 `app/providers.tsx`.
- `dev` 스크립트는 `next dev --webpack` 고정 — Turbopack은 레퍼런스 프로젝트에서
  CPU 폭주 이력이 있다. 떼지 말 것.
- `globals.css`의 `@import "tailwindcss" source("../")`는 스캔 범위를 www/로 못박는
  장치다 — 지우면 dev 서버가 저장소 전체를 감시한다.
- 검증 수단은 `pnpm run typecheck`뿐(테스트 러너 없음). `npx tsc` 직접 실행 금지 —
  반드시 package.json 스크립트로.
- 공개 페이지(크리에이터 프로필 등)는 SSR을 유지한다 — 프로그래매틱 SEO가 핵심 전략
  (collabstr-analysis §7).
- **스택 확정(2026-08-10)**: 현 스택 외 라이브러리 추가 금지. UI 착수 시 shadcn/ui,
  첫 폼 구현 시 zod만 예정(선제 설치 금지). React Hook Form은 도입하지 않는다 —
  폼은 FormData 패턴/React 19 form actions(REACT_RULES 정본). 고복잡도 폼(수십 필드
  +실시간 필드별 검증)이 실제 등장하면 그 화면에 한정해 재검토.

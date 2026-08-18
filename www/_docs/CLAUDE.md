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
- 페르소나 랜딩(`/for/[persona]`, 갭 #13)의 콘텐츠 정본은 `lib/personas.ts`다 — 페이지는
  렌더만 한다. **구현된 기능만 서술하고 성과 수치·고객 사례는 쓰지 않는다**(실적 확보 전
  허위 표기 방지). 새 페르소나는 배열에 항목을 더하면 sitemap·상호 링크가 따라온다.
- **온보딩 안내는 계정 유형별로 다른 컴포넌트다** — 크리에이터는 `onboarding-checklist.tsx`
  (실제 등록 상태를 조회해 진행률, 갭 #58), 브랜드는 `brand-onboarding.tsx`(주문 0건일 때
  주문 목록 자리에 첫 걸음 안내, 갭 #78). 브랜드 쪽은 조회할 "완성도"가 없어 정적 안내다.
- 공개 페이지(크리에이터 프로필 등)는 SSR을 유지한다 — 프로그래매틱 SEO가 핵심 전략
  (collabstr-analysis §7).
- 홈 검색 필터의 **URL 표현 정본은 `lib/search-filters.ts`**(가격대 `"하한-상한"` 파싱,
  홈 href, 백엔드 쿼리 조립) — 홈과 빈 결과 안내(갭 #48)가 함께 쓴다. 새 필터를 더하면
  여기부터 고친다.
- **비교 화면의 지표 조합 정본은 `lib/creator-metrics.ts`**(갭 #86·#87) — 행 단위로
  공개 프로필 API 2종을 읽어 팔로워·참여율(채널 중 최고값)·거래 실적을 얹는다.
  백엔드 목록 응답에 지표를 실어달라고 하지 말 것(campaign CLAUDE.md에 근거).
  참여율은 로그인 게이트(#14) 뒤라 게스트가 볼 수 있는 화면에서는 조회하지 않고
  가입 유도만 한다. 없는 지표는 0이 아니라 "—"(#65 원칙).
- 전역 404는 `app/not-found.tsx`, 에러 경계는 `app/error.tsx` — **Next 16의 error 경계는
  `reset`이 아니라 `retry` prop을 받는다**(구버전 예제를 그대로 쓰면 타입 오류).
- **인쇄용 화면**(계약 조건 확인서 갭 #52, 지급명세서)은 `globals.css`의 `@media print`가
  헤더·푸터와 `.no-print` 요소를 지운다 — 조작 버튼에는 `no-print` 클래스를 준다.
- **정책을 설명하는 공개 페이지**(`/how-it-works` 갭 #47, 페르소나 랜딩, `/terms`)는
  **구현된 규칙만** 적고 **설정으로 바뀌는 값은 숫자로 박지 않는다** — 수수료율은
  `core/config.py`의 `ORDER_*_FEE_PERCENT`라 "결제 화면에서 확인"으로 넘긴다.
  반대로 도메인이 강제하는 규칙(72h 기한, 원천징수 3.3%)은 그대로 적는다.
  새 공개 페이지는 sitemap(`app/sitemap.ts`)·푸터(`components/site-footer.tsx`) 등록까지 한다.
- **블로그(갭 #69)의 콘텐츠 정본은 `lib/blog.ts`** — 페르소나 랜딩과 같은 원칙으로 페이지
  (`/blog`·`/blog/[slug]`)는 렌더만 한다. 새 글은 배열에 항목을 더하면 목록·sitemap·
  이전/다음 링크가 따라온다. 발행일은 절대 날짜(YYYY-MM-DD)로 적고, 실적 수치·고객 사례를
  만들어 넣지 않으며 crecity 기능은 구현된 것만 언급한다.
- **OG 이미지(갭 #46)**: 프로필 공유 카드는 `app/creators/[slug]/opengraph-image.tsx`가
  `next/og`로 그린다. 한글을 그리려면 폰트를 직접 실어야 한다 — `assets/Pretendard-{Bold,Regular}.otf`
  (OFL, 고지 파일 동봉)를 **모듈 스코프에서 한 번만** `readFile`한다. `ImageResponse`는
  **ttf·otf·woff만** 지원하고(woff2 불가) satori 렌더러라 **flex 레이아웃만** 된다
  (자식이 둘 이상인 요소에 `display:"flex"` 명시 필수, CSS 변수 사용 불가 — 색은 리터럴).
  `twitter:image`는 Next가 자동 파생하므로 `twitter-image.tsx`를 따로 만들지 않는다.
- **스택 확정(2026-08-10)**: 현 스택 외 라이브러리 추가 금지. UI 착수 시 shadcn/ui,
  첫 폼 구현 시 zod만 예정(선제 설치 금지). React Hook Form은 도입하지 않는다 —
  폼은 FormData 패턴/React 19 form actions(REACT_RULES 정본). 고복잡도 폼(수십 필드
  +실시간 필드별 검증)이 실제 등장하면 그 화면에 한정해 재검토.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# CLAUDE.md — creator (스포크)

크리에이터 프로필·판매 패키지 도메인(마켓플레이스 공급 측).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| profile (myself) | `GET /creator/myself` | 자기소개 |
| profile_registration | `POST /creator/profiles` | 프로필 등록 → PENDING(심사 대기). **로그인 필수(CREATOR 계정만 403)**, 1인 1프로필(409), 슬러그 형식은 domain `Slug` VO, 중복 409 |
| profile_lookup | `GET /creator/profiles/{slug}` | 공개 조회(SSR 데이터 소스). REJECTED도 직접 조회 가능(목록 제외만) |
| package_management | `POST/GET /creator/profiles/{slug}/packages` · `PUT/DELETE /creator/packages/{id}` | 가격 공개 패키지 CRUD. 플랫폼은 `PackagePlatform`(IG·YT·틱톡·네이버 블로그·UGC), 가격은 `Price` VO(양수), 목록은 가격 오름차순. **쓰기는 로그인+소유자만(403)** — 조회는 공개 |
| my_profile_lookup | `GET /creator/my/profile` | 로그인 사용자의 프로필 조회(대시보드용) — 없으면 404 |
| profile_listing | `GET /creator/profiles` | 마켓플레이스 공개 목록(SSR 데이터 소스) — APPROVED만, 최신 등록순. `category`(primary_category 일치)·`limit`(≤50)·`offset`, 응답은 `items`+`total`(bio 제외 카드 필드) |

- 엔티티: `CreatorProfile`(+`ProfileStatus`, `user_id` 소유 계정·`is_owned_by`) ·
  `CreatorPackage`(+`PackagePlatform`). 현재 사용자는 허브 `get_current_user`로 얻는다
  (auth 직접 import 금지). `user_id`는 auth users 논리 참조 — 스포크 경계라 DB FK 없음,
  NULL은 소셜 로그인 도입 전 레거시 행뿐.
- 새 ORM 추가 시 `crecity/alembic/env.py`에 import 한 줄 등록 필수(오토젠 대상).
- 예정: 심사(admin 연동) · 키워드 검색 · 포트폴리오.

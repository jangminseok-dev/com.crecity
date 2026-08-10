# CLAUDE.md — creator (스포크)

크리에이터 프로필·판매 패키지 도메인(마켓플레이스 공급 측).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| profile (myself) | `GET /creator/myself` | 자기소개 |
| profile_registration | `POST /creator/profiles` | 프로필 등록 → PENDING(심사 대기). 슬러그 형식은 domain `Slug` VO, 중복은 409 |
| profile_lookup | `GET /creator/profiles/{slug}` | 공개 조회(SSR 데이터 소스). REJECTED도 직접 조회 가능(목록 제외만) |
| package_management | `POST/GET /creator/profiles/{slug}/packages` · `PUT/DELETE /creator/packages/{id}` | 가격 공개 패키지 CRUD. 플랫폼은 `PackagePlatform`(IG·YT·틱톡·네이버 블로그·UGC), 가격은 `Price` VO(양수), 목록은 가격 오름차순 |
| profile_listing | `GET /creator/profiles` | 마켓플레이스 공개 목록(SSR 데이터 소스) — APPROVED만, 최신 등록순. `category`(primary_category 일치)·`limit`(≤50)·`offset`, 응답은 `items`+`total`(bio 제외 카드 필드) |

- 엔티티: `CreatorProfile`(+`ProfileStatus`) · `CreatorPackage`(+`PackagePlatform`) — user_id 연결과 수정/삭제 소유권 검증은 auth 소셜 로그인 단계에서 추가.
- 새 ORM 추가 시 `crecity/alembic/env.py`에 import 한 줄 등록 필수(오토젠 대상).
- 예정: 심사(admin 연동) · 키워드 검색 · 포트폴리오.

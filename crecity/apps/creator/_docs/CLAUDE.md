# CLAUDE.md — creator (스포크)

크리에이터 프로필·판매 패키지 도메인(마켓플레이스 공급 측).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| profile (myself) | `GET /creator/myself` | 자기소개 |
| profile_registration | `POST /creator/profiles` | 프로필 등록 → PENDING(심사 대기). 슬러그 형식은 domain `Slug` VO, 중복은 409 |
| profile_lookup | `GET /creator/profiles/{slug}` | 공개 조회(SSR 데이터 소스). REJECTED도 직접 조회 가능(목록 제외만) |

- 엔티티: `CreatorProfile`(+`ProfileStatus`) — user_id 연결은 auth 소셜 로그인 단계에서 추가.
- 새 ORM 추가 시 `crecity/alembic/env.py`에 import 한 줄 등록 필수(오토젠 대상).
- 예정: 패키지(가격 공개 상품) CRUD · 심사(admin 연동) · 목록/검색(APPROVED만).

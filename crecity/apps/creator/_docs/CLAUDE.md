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
| profile_update | `PUT /creator/my/profile` | 내 프로필 수정 — 슬러그(SEO 단위)·심사 상태 불변, 내용 필드만 |
| portfolio_management | `POST /creator/my/portfolio` · `DELETE /creator/my/portfolio/{id}` · `GET /creator/profiles/{slug}/portfolio` | 포트폴리오 사진 — 업로드는 multipart(`ImageFile` VO: JPG·PNG·WebP·5MB 이하 422), 프로필당 12장(409), 쓰기는 소유자만(403), 목록은 공개(등록순). 파일은 `PortfolioFileStorage` 포트(로컬 디스크 구현 — `UPLOAD_DIR`, main.py가 `/uploads` 정적 서빙) |
| analytics_management | `POST·GET /creator/my/analytics` · `DELETE /creator/my/analytics/{platform}` · `GET /creator/profiles/{slug}/analytics` | 채널 분석 지표(§9.2, 갭 #14) — 자가입력(팔로워·참여율‰) + 스크린샷 인증(`ImageFile` VO), 프로필당 플랫폼 1행(재제출=갱신), UGC 제외 4채널. **공개 열람은 로그인 필수(401 — 가입 게이트)**. 프로필 조회에 `followers_total` 합계 배지 |
| profile_listing | `GET /creator/profiles` · `GET /creator/categories` | 마켓플레이스 공개 목록(SSR 데이터 소스) — APPROVED만, 최신 등록순. `category`·`q`(이름·태그라인 부분 일치)·`platform`·`price_min/max`(해당 조건 패키지 EXISTS)·`location`(부분 일치)·`limit`(≤50)·`offset`, 응답은 `items`+`total`(목록·총계 동일 조건 — §3.1 검색 필터, 갭 #9). categories는 필터 칩용 중복 제거 목록 |

- 엔티티: `CreatorProfile`(+`ProfileStatus`, `user_id` 소유 계정·`is_owned_by`) ·
  `CreatorPackage`(+`PackagePlatform`). 현재 사용자는 허브 `get_current_user`로 얻는다
  (auth 직접 import 금지). `user_id`는 auth users 논리 참조 — 스포크 경계라 DB FK 없음,
  NULL은 소셜 로그인 도입 전 레거시 행뿐.
- 새 ORM 추가 시 `crecity/alembic/env.py`에 import 한 줄 등록 필수(오토젠 대상).
- (심사는 admin 앱. 키워드 검색·프로필 수정·포트폴리오는 2026-08-10 구축 완료)

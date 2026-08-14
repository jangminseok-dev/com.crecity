# CLAUDE.md — creator (스포크)

크리에이터 프로필·판매 패키지 도메인(마켓플레이스 공급 측).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| profile (myself) | `GET /creator/myself` | 자기소개 |
| profile_registration | `POST /creator/profiles` | 프로필 등록 → PENDING(심사 대기). **로그인 필수(CREATOR 계정만 403)**, 1인 1프로필(409), 슬러그 형식은 domain `Slug` VO, 중복 409 |
| profile_lookup | `GET /creator/profiles/{slug}` | 공개 조회(SSR 데이터 소스). REJECTED도 직접 조회 가능(목록 제외만). **거래 실적**(갭 #66)을 허브 `CreatorTradeStatsPort`로 실어 준다 — 받은 주문이 0건이면 null(신규를 깎지 않는다) |
| package_management | `POST/GET /creator/profiles/{slug}/packages` · `PUT/DELETE /creator/packages/{id}` | 가격 공개 패키지 CRUD. 플랫폼은 `PackagePlatform`(IG·YT·틱톡·네이버 블로그·UGC), 가격은 `Price` VO(양수), 목록은 가격 오름차순. 표준계약 구조화 필드 `revision_limit`(0~10)·`usage_rights`(≤300자, §3.3·§9.2 — 주문이 스냅샷). **쓰기는 로그인+소유자만(403)** — 조회는 공개 |
| my_profile_lookup | `GET /creator/my/profile` | 로그인 사용자의 프로필 조회(대시보드용) — 없으면 404 |
| profile_update | `PUT /creator/my/profile` | 내 프로필 수정 — 슬러그(SEO 단위)·심사 상태 불변, 내용 필드만 |
| portfolio_management | `POST /creator/my/portfolio` · `DELETE /creator/my/portfolio/{id}` · `GET /creator/profiles/{slug}/portfolio` | 포트폴리오 사진 — 업로드는 multipart(`ImageFile` VO: JPG·PNG·WebP·5MB 이하 422), 프로필당 12장(409), 쓰기는 소유자만(403), 목록은 공개(등록순). 파일은 `PortfolioFileStorage` 포트(로컬 디스크 구현 — `UPLOAD_DIR`, main.py가 `/uploads` 정적 서빙) |
| faq_management | `POST·GET /creator/my/faqs` · `DELETE /creator/my/faqs/{id}` · `GET /creator/profiles/{slug}/faqs` | 프로필 FAQ(§2.1-9, 갭 #24) — 크리에이터 자가 작성 Q&A, 프로필당 10개(409), 질문 200·답변 2000자(422), 열람은 공개(등록순 아코디언) |
| analytics_management(오디언스) | — | 채널 지표에 **오디언스**(§2.1-6, 갭 #67)를 함께 받는다: 주 지역은 `profile_analytics.top_audience_region`(단일값 컬럼), 연령·성별 비율은 **다중값이라 `profile_audience_breakdown` 조인 테이블**(3NF). 구간은 `audience_breakdown.py`가 고정(AGE 5·GENDER 3), 비율은 퍼밀. **같은 축 합 100% 초과 422**, 재제출 시 통째 교체. multipart라 JSON 문자열로 받는다 |
| analytics_management | `POST·GET /creator/my/analytics` · `DELETE /creator/my/analytics/{platform}` · `GET /creator/profiles/{slug}/analytics` | 채널 분석 지표(§9.2, 갭 #14) — 자가입력(팔로워·참여율‰) + 스크린샷 인증(`ImageFile` VO), 프로필당 플랫폼 1행(재제출=갱신), UGC 제외 4채널. **공개 열람은 로그인 필수(401 — 가입 게이트)**. 프로필 조회에 `followers_total` 합계 배지 |
| order_acceptance | `PUT /creator/my/profile/accepting-orders` | 주문 수신 켜기·끄기(갭 #64) — `creator_profiles.accepting_orders`는 **심사 상태와 직교**한 별도 컬럼이다(휴가 중 72h 무응답 랭킹 페널티 회피). 끄면 목록에서 빠지고(`_listing_conditions` 기본 조건) **`PackageSummaryGateway`가 None을 반환해 주문이 차단된다** — payment·order를 건드리지 않고 기존 '주문 불가' 경로를 태우는 방식. 프로필 직접 조회·SEO는 그대로 |
| profile_view | `POST /creator/profiles/{slug}/views` · `GET /creator/my/profile/views` | 프로필 조회수(갭 #57) — 기록은 **브라우저가 호출**(비로그인 허용, 없는 슬러그도 204로 조용히 무시)해 크롤러 트래픽을 대체로 배제한다. 열람은 **항상 본인 기준**(남의 조회수 불가). 낱건 로그 없이 `profile_view_daily`(profile_id+view_date unique)에 **UPSERT로 증가** — 조회 없던 날은 유스케이스가 0으로 채워 30일 추이를 만든다 |
| profile_listing | `GET /creator/profiles` · `GET /creator/categories` | 마켓플레이스 공개 목록(SSR 데이터 소스) — APPROVED만, 기본 최신 등록순. `category`·`q`(이름·태그라인 부분 일치)·`platform`·`price_min/max`(해당 조건 패키지 EXISTS)·`location`(부분 일치)·`limit`(≤50)·`offset`, 응답은 `items`+`total`(목록·총계 동일 조건 — §3.1 검색 필터, 갭 #9). `sort`는 `ProfileSort`(latest·price_asc·price_desc — 갭 #45, 가격은 최저 패키지 가격·NULL은 뒤로). categories는 필터 칩용 중복 제거 목록 |

- `ProfileStatus.DELETED`는 계정 탈퇴 표식(갭 #33) — 목록 제외 + **공개 조회도 404**.
- 엔티티: `CreatorProfile`(+`ProfileStatus`, `user_id` 소유 계정·`is_owned_by`) ·
  `CreatorPackage`(+`PackagePlatform`). 현재 사용자는 허브 `get_current_user`로 얻는다
  (auth 직접 import 금지). `user_id`는 auth users 논리 참조 — 스포크 경계라 DB FK 없음,
  NULL은 소셜 로그인 도입 전 레거시 행뿐.
- **정량 vetting(갭 #16)**: `domain/value_objects/vetting_check.py`가 채널 지표로 기준 충족을
  판정해 심사 게이트웨이가 허브 `ProfileReviewSummary`에 실어 보낸다. 기준값은 도메인이 아니라
  `core/config`(`VETTING_MIN_FOLLOWERS`·`VETTING_MIN_ENGAGEMENT_PERMILLE`)가 소유하며,
  **자동 승인·반려는 하지 않는다**(자가입력 지표 — 운영자 판단 보조).
- 새 ORM 추가 시 `crecity/alembic/env.py`에 import 한 줄 등록 필수(오토젠 대상).
- (심사는 admin 앱. 키워드 검색·프로필 수정·포트폴리오는 2026-08-10 구축 완료)

# CLAUDE.md — campaign (스포크)

역경매 도메인 — 브랜드가 공고를 올리고 크리에이터가 자체 견적으로 지원한다(수요 측 마켓).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| herald (myself) | `GET /campaign/myself` | 자기소개 |
| campaign_posting | `POST /campaign/campaigns` · `POST /campaign/campaigns/{id}/close` | 공고 등록(**브랜드만 403**, OPEN 시작) · 마감(소유 브랜드만 403, 재마감 409 — 도메인 검증) |
| campaign_listing | `GET /campaign/campaigns` · `/{id}` · `GET /campaign/my/campaigns` | OPEN 목록·상세(로그인 필수)·브랜드 내 공고 |
| campaign_application | `POST·GET /campaign/campaigns/{id}/applications` | 지원(**크리에이터만·프로필 필수 403**, 공고당 1회 409, 마감 공고·마감일 경과 409) · 지원자 열람(**공고 브랜드만 403**). 지원 저장과 **같은 트랜잭션**으로 `campaign.application_received`를 적재해 공고를 올린 브랜드에게 알린다(갭 #73) |
| campaign_application (내 지원) | `GET /campaign/my/applications` | 크리에이터 본인의 지원 내역 — 최신순(**크리에이터만 403**). 응답에 공고 제목·상태·마감일을 함께 실어 **화면이 상태를 파생**한다(갭 #103) |
| campaign_deadline_sweep | (HTTP 없음) | 지원 마감일 스캔 — `scripts/campaign_deadline_sweep.py`를 cron이 주기 실행(갭 #27). 마감일 경과 OPEN 공고 → CLOSED |

- **지원 상태 컬럼을 만들지 않는다(갭 #103)**: "선정"은 `campaign_applications.order_id`,
  "미선정"은 공고의 `status`·`deadline_at`에서 나온다 — 같은 사실을 두 곳에 두면 어긋난다.
  공고가 사라진 지원은 내역에서 제외한다(보여줄 맥락이 없다).
- **지원자 정렬·필터(갭 #70)**: `ApplicationSort`(oldest·latest·price_asc·price_desc)
  + `only_open`(미수락만). 캠페인이 소유한 값으로만 정렬한다 — 팔로워·평점은 다른 스포크
  소유라 DB 정렬이 스포크 경계를 넘는다(갭 #45와 같은 이유).
- **적합 크리에이터 추천(갭 #99)도 백엔드 미관여** — 공고 소유 브랜드 화면
  (`campaign-creator-match.tsx`)이 공고의 타겟 조건(플랫폼·카테고리·지역)+예산을
  기존 공개 목록 필터(`GET /creator/profiles?platform=&category=&location=&price_max=`)로
  변환해 후보 4명을 보여준다. **표시만 한다**(자동 초대·발송 없음 — 수락 강요 방지),
  이미 지원한 크리에이터는 제외, 후보 없으면 섹션 미렌더. Instant Creator Match(§3.2)의
  규칙 기반판 — #40의 LLM 없는 대체.
- **지원자 결제 전 문의(갭 #96)도 백엔드 미관여** — 지원자 카드의 문의 버튼이 chat의
  기존 대화 생성(`POST /chat/conversations`)을 그대로 쓴다(프로필 문의와 동일 컴포넌트).
- **지원자 나란히 비교(갭 #86)는 백엔드 미관여** — 화면(`campaign-applicant-compare.tsx`)이
  지원자별 공개 프로필 API(`/creator/profiles/{slug}`·`/analytics`)를 조합한다(#83과 같은
  원칙). 지원자 목록 응답에 팔로워·거래 실적을 실으려고 허브 포트를 늘리지 말 것 —
  전부 공개 프로필에 이미 있는 값이고, 비교 뷰를 열 때만 조회하면 충분하다.
- 엔티티: `Campaign`(+`CampaignPlatform`·`CampaignStatus`, `close`·`expire` 전이) ·
  `CampaignApplication`. 플랫폼 enum은 스포크 독립 원칙상 자체 정의(creator enum 미참조).
- **마감일·타겟팅(갭 #27·#28)**: `deadline_at`(선택)이 지나면 스윕이 CLOSED로 전이하고,
  스윕 주기와 무관하게 `ensure_open_for_application(now)`가 지원을 막는다(마감일이 정본).
  `target_category`·`target_location`은 지원 자격 제한이 아니라 매칭 안내용 표시 필드.
- 테이블: `campaigns` · `campaign_applications`(campaign_id+creator_user_id unique).
- 지원자 표시(이름·슬러그)는 허브 `CreatorRefPort.get_creator_by_user_id`로 실시간 해석(스냅샷 없음 — 3NF).
- **지원 수락 → 주문 연결(갭 #7, 2026-08-11)**: 허브 `CampaignApplicationPort` 구현
  (`CampaignApplicationGateway`) 제공 — payment(수락 결제 준비·확정 표시)와 order(견적·당사자
  해석)가 소비한다. `campaign_applications.order_id`(논리 참조)가 수락 완료 표식이며
  재수락을 차단한다(`is_payable`). 수락 흐름 자체는 §3 결제 경유(커스텀 오퍼와 동일 패턴).
- 예정: 공고 마감일 자동 처리 · 타겟팅 필드.

# CLAUDE.md — campaign (스포크)

역경매 도메인 — 브랜드가 공고를 올리고 크리에이터가 자체 견적으로 지원한다(수요 측 마켓).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| herald (myself) | `GET /campaign/myself` | 자기소개 |
| campaign_posting | `POST /campaign/campaigns` · `POST /campaign/campaigns/{id}/close` | 공고 등록(**브랜드만 403**, OPEN 시작) · 마감(소유 브랜드만 403, 재마감 409 — 도메인 검증) |
| campaign_listing | `GET /campaign/campaigns` · `/{id}` · `GET /campaign/my/campaigns` | OPEN 목록·상세(로그인 필수)·브랜드 내 공고 |
| campaign_application | `POST·GET /campaign/campaigns/{id}/applications` | 지원(**크리에이터만·프로필 필수 403**, 공고당 1회 409, 마감 공고 409) · 지원자 열람(**공고 브랜드만 403**) |

- 엔티티: `Campaign`(+`CampaignPlatform`·`CampaignStatus`, `close` 전이) · `CampaignApplication`.
  플랫폼 enum은 스포크 독립 원칙상 자체 정의(creator enum 미참조).
- 테이블: `campaigns` · `campaign_applications`(campaign_id+creator_user_id unique).
- 지원자 표시(이름·슬러그)는 허브 `CreatorRefPort.get_creator_by_user_id`로 실시간 해석(스냅샷 없음 — 3NF).
- **지원 수락 → 주문 연결(갭 #7, 2026-08-11)**: 허브 `CampaignApplicationPort` 구현
  (`CampaignApplicationGateway`) 제공 — payment(수락 결제 준비·확정 표시)와 order(견적·당사자
  해석)가 소비한다. `campaign_applications.order_id`(논리 참조)가 수락 완료 표식이며
  재수락을 차단한다(`is_payable`). 수락 흐름 자체는 §3 결제 경유(커스텀 오퍼와 동일 패턴).
- 예정: 공고 마감일 자동 처리 · 타겟팅 필드.

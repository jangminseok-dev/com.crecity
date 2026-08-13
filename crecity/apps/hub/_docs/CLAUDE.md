# CLAUDE.md — hub (허브)

앱 간 협력의 단일 교차점. 계약(포트·DTO)만 소유하고 구체 스포크를 import하지 않는다.
현재 슬라이스: dispatcher(`GET /hub/myself`).
스포크가 소비할 포트는 `hub/app/ports/`에, DTO는 `hub/app/dtos/`에 둔다.

## 공개된 교차 협력 계약

| 계약 | 구성 | 구현 | 소비 |
|---|---|---|---|
| 현재 사용자 | `AccessTokenVerifier` 포트 + `VerifiedUser` DTO(roles·permissions 포함) + `get_current_user`·`require_permission` DI(`dependencies/current_user_provider.py`) | auth(`JwtAccessTokenVerifier`) — **main.py가 `register_access_token_verifier`로 조립** | creator·order 보호 라우터(`Depends(get_current_user)` 401 · `Depends(require_permission("코드"))` 403) |
| 패키지 요약 | `PackageSummaryPort` 포트 + `PackageSummary` DTO(`dependencies/package_summary_provider.py`) | creator(`CreatorPackageSummaryGateway`) — main.py가 `register_package_summary_port`로 조립 | order 주문 생성 검증(가격·적립 대상 creator_user_id) |
| 프로필 심사 | `ProfileReviewPort` 포트 + `ProfileReviewSummary` DTO(`dependencies/profile_review_provider.py`) | creator(`CreatorProfileReviewGateway`) — main.py가 `register_profile_review_port`로 조립 | admin 심사 슬라이스(대기 목록·승인/반려 전이) |
| 결제 완료 주문 생성 | `OrderPlacementPort` 포트 + `PlacedOrder` DTO(`dependencies/order_placement_provider.py`) | order(`PaidOrderPlacementGateway`) — main.py가 `register_order_placement_port`로 조립. 금액 불일치 시 None(생성 거부) | payment 승인 후 주문 생성(§3 — 실패 시 PG 취소 보정) |
| 주문 당사자 조회 | `OrderParticipantsPort` 포트 + `OrderParticipants` DTO(`dependencies/order_participants_provider.py`) | order(`OrderParticipantsGateway`) | review 리뷰 자격 검증(완료 주문·브랜드 본인) |
| 크리에이터 참조 조회 | `CreatorRefPort` 포트 + `CreatorRef` DTO(`dependencies/creator_ref_provider.py`) | creator(`CreatorRefGateway`) | review 공개 조회(슬러그 → 계정) · campaign 지원자 표시 · chat 상대 표시 — §5 "크리에이터 요약 조회" 실현 |
| 회원 디렉토리 조회 | `UserDirectoryPort` 포트 + `UserRef` DTO(`dependencies/user_directory_provider.py`) | auth(`UserDirectoryGateway`) | chat 상대(브랜드) 이름 표시 — §5 "회원 디렉토리 조회" 실현 |
| 커스텀 오퍼 조회·확정 | `CustomOfferPort` 포트 + `CustomOfferSummary` DTO(`dependencies/custom_offer_provider.py`) | chat(`CustomOfferGateway`) — main.py가 `register_custom_offer_port`로 조립 | payment 오퍼 결제 준비·PAID 처리 · order 커스텀 주문 생성(가격·당사자 해석) |
| 크레딧 잔액 조회 | `CreditBalancePort` 포트(`dependencies/credit_balance_provider.py`) | order(`OrderCreditBalanceGateway`) — main.py가 `register_credit_balance_port`로 조립 | payment 체크아웃 준비(크레딧 적용액 확정 — 실차감·재검증은 주문 생성 트랜잭션이 수행) |
| 캠페인 지원 조회·확정 | `CampaignApplicationPort` 포트 + `CampaignApplicationSummary` DTO(`dependencies/campaign_application_provider.py`) | campaign(`CampaignApplicationGateway`) — main.py가 `register_campaign_application_port`로 조립 | payment 지원 수락 결제 준비·order_id 기록 · order 지원 수락 주문 생성(견적·당사자 해석) — 갭 #7 |
| 주문 금액 변경 | `OrderAdjustmentPort` 포트 + `OrderAdjustmentSummary` DTO(`dependencies/order_adjustment_provider.py`) | order(`OrderAdjustmentGateway`) — main.py가 `register_order_adjustment_port`로 조립 | payment 추가 결제 준비·반영(갭 #31 — 반영 실패 시 None → PG 취소 보정) |
| 인출 운영 처리 | `WithdrawalSettlementPort` 포트 + `WithdrawalSummary`·`AnnualPayoutSummary` DTO(`dependencies/withdrawal_settlement_provider.py`) | order(`OrderWithdrawalSettlementGateway`) | admin 인출 처리(완료·실패) + 연간 지급 집계(갭 #2) |
| 분쟁 판정 | `DisputeResolutionPort` 포트 + `DisputeSummary` DTO(`dependencies/dispute_resolution_provider.py`) | order(`OrderDisputeResolutionGateway`) — main.py가 `register_dispute_resolution_port`로 조립 | admin 분쟁 중재(대기 목록·환불/지급/기각 판정 — 갭 #4) |
| 활성 주문 확인 | `ActiveOrderPort`(`dependencies/active_order_provider.py`) | order(`OrderActiveOrderGateway`) | auth 계정 탈퇴 차단(갭 #33) |
| 프로필 비활성화 | `ProfileDeactivationPort`(`dependencies/profile_deactivation_provider.py`) | creator(`CreatorProfileDeactivationGateway`) | auth 탈퇴 시 공개 프로필 DELETED 처리 |
| Outbox 이벤트 중계 | `OutboxEvent` DTO(`app/dtos/outbox_event_dto.py`, `"<도메인>.<사건>"` 규약) + `outbox_events` 테이블 + `enqueue_events`/`fetch_unpublished`/`mark_published`(`adapter/outbound/pg/outbox_pg_store.py` — 전부 무커밋, 호출자 트랜잭션 참여) | (허브 자체 소유 — 조립 불필요) | 발행: order 리포지토리·creator 심사 게이트웨이 / 소비: notification 워커(BOUNDARIES §1) |

- 조립 규칙: 허브는 스포크를 모르므로 구현체 등록은 항상 main.py(조립 루트) 몫이다.

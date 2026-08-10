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

- 조립 규칙: 허브는 스포크를 모르므로 구현체 등록은 항상 main.py(조립 루트) 몫이다.

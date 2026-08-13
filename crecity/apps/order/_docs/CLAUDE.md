# CLAUDE.md — order (스포크)

주문 상태머신 · 에스크로/잔액 원장(돈의 장부 — BOUNDARIES §3). PG 접점은 payment 앱(예정) 몫.

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| bookkeeper (myself) | `GET /order/myself` | 자기소개 |
| order_placement | (HTTP 없음 — 결제 경유 전용) | 주문 생성 — payment 승인 후 허브 `OrderPlacementPort`(order 구현 `PaidOrderPlacementGateway`)로만 호출된다. 커스텀 오퍼 주문(`place_custom`)은 `CustomOfferPort`로, 캠페인 지원 수락 주문(`place_application`)은 `CampaignApplicationPort`로 가격·당사자를 해석하며 package_id가 NULL. 금액·수수료율(§7-4)·패키지 제목 스냅샷, 72h 수락 마감, 에스크로 예치 기입. 결제 금액과 현재 계산 불일치 시 생성 거부(None). 크레딧 사용분(`credit_used_krw`)은 advisory lock 잔액 재검증 + CREDIT_SPENT 기입을 주문 생성과 단일 트랜잭션으로 — 부족 시 생성 거부. 장바구니(`place_cart`, §3.8)는 주문 N건+예치 N건을 `create_many` **단일 트랜잭션**으로 — 불가 패키지·크레딧 부족 시 전체 거부(부분 생성 없음) |
| order_progress | `POST /order/orders/{id}/accept·reject·submit·request-revision·approve` | 상태 전이 — 규칙·행위자 검증은 도메인 `Order`가 강제(403/409). 거절→크레딧 환불, 승인→적립+수수료 확정 |
| deliverable_submission | `POST /order/orders/{id}/deliverables/files·links` · `GET /order/orders/{id}/deliverables` | 납품물(파일·링크) — 등록은 **IN_PROGRESS의 크리에이터만**(도메인 `ensure_can_attach_deliverable`), 열람은 당사자만(403). append-only(분쟁 근거 보존), 파일은 `/uploads/deliverables/` 로컬 저장(이미지·영상·PDF·ZIP, 100MB). 링크는 게시물 본문(`caption`, 3000자, 선택)을 함께 받아 **광고 표기 자동 검수**(갭 #17) |
| order_cancellation | `POST /order/orders/{id}/cancel-request·cancel-consent·cancel-decline` | 양측 합의 취소 — 요청은 IN_PROGRESS·IN_REVIEW의 당사자 누구나(중복 409), 동의·거부는 **상대방만**(403). 동의 시 CANCELLED + 브랜드 전액 크레딧 환불(단일 트랜잭션). `orders.cancel_requested_by`가 대기 상태 표현 |
| order_adjustment | `POST·GET /order/orders/{id}/adjustments` · `POST /order/adjustments/{id}/decline` | 진행 중 금액 변경(§3.8·§6, 갭 #31) — 요청은 **IN_PROGRESS·IN_REVIEW의 크리에이터만**(대기 중 중복 409), 거절은 브랜드만. **수락은 추가 결제**(payment `/checkouts/adjustment` → 허브 `OrderAdjustmentPort`로 주문 증액+증가분 예치 단일 트랜잭션). 감액은 미지원(합의 취소로) |
| order_lookup | `GET /order/orders` · `GET /order/orders/{id}` | 내 주문 목록(최신순)·상세 — **당사자만(403)** |
| balance_lookup | `GET /order/balance` | 내 잔액 = 적립성 기입 합 − 차감성 기입 합 |
| withdrawal_request | `POST/GET /order/withdrawals` | 크리에이터 적립금 인출 — 요청 시 잔액 재검증+차감 기입(WITHDRAWAL)을 advisory lock 단일 트랜잭션으로(과인출 차단), 원천징수 3.3% 세액·실지급액 스냅샷. 운영 처리(완료/실패·복원)는 허브 `WithdrawalSettlementPort`(order 구현 게이트웨이)로 admin이 수행 |
| deadline_sweep | (HTTP 없음) | 72h 만료 스캔 — `scripts/order_deadline_sweep.py`를 cron이 주기 실행. 수락 만료→환불, 검토 만료→자동 승인 |

## 도메인 규칙 (BOUNDARIES §4 · collabstr §3.8)

```
PENDING_ACCEPT ──수락──▶ IN_PROGRESS ──제출──▶ IN_REVIEW ──승인/72h──▶ COMPLETED
      │                                     │
      ├─ 거절/72h 만료 ─▶ REFUNDED           └─ 수정 요청 ─▶ IN_PROGRESS (무제한)

IN_PROGRESS·IN_REVIEW ──취소 요청→상대 동의──▶ CANCELLED (브랜드 전액 크레딧 환불)
                        └─ 상대 거부 ─▶ 요청 해제(주문 계속)
```

- **제출은 납품물 ≥1건이 전제**(`Order.submit`의 `deliverable_count`) — 상태 전이가 아니라
  결과물 인도이며, 에스크로 승인·분쟁 판단의 근거를 남긴다(갭 #3, 2026-08-11).
- **광고 표기 검수(갭 #17)**: `domain/value_objects/ad_disclosure.py`가 본문에서 대가성 표시
  (광고·협찬·PPL·제공받음·sponsored·#ad 등)를 찾는다. 판정은 **파생값이라 저장하지 않고**
  `Deliverable.ad_disclosure_ok`로 매번 계산한다(링크만 대상, 파일은 None). **경고일 뿐
  제출·승인을 막지 않는다** — 오판정으로 인도를 막지 않기 위함.
- 상태 전이·수수료 계산은 **순수 도메인**(`Order`) — 정수 원 단위 내림, 부동소수 금지.
- **수정 요청은 스냅샷된 횟수까지**(`revision_limit`/`revisions_used`, 갭 #29) — 초과 409.
  `usage_rights`와 함께 주문 생성 시 패키지에서 스냅샷(오퍼·지원 수락 주문은 기본값 2회).
- 브랜드 결제 총액 = 가격 + 브랜드 수수료(예치액) · 크리에이터 적립 = 가격 − 크리에이터 수수료.
  요율은 `core/config.py`(`ORDER_*_FEE_PERCENT`, 초기 10/10) — 주문 생성 시점 스냅샷.
- **전이 + 원장 기입 + Outbox 이벤트 = 단일 트랜잭션**(`OrderRepository.create/save_transition`의
  `events` 인자 — BOUNDARIES §1). 이벤트는 `app/events.py`의 `order_event`로 만든다
  (order.placed/accepted/rejected/submitted/revision_requested/completed/
  cancel_requested/cancelled/cancel_declined — notification이 소비).
- **수락 만료 페널티(갭 #32)**: 72h 무응답 만료는 `accept_expired` 표식을 남겨 거절 환불과
  구분한다 — 인기 랭킹 점수 = 성사 주문 − 만료×`RANKING_ACCEPT_EXPIRY_PENALTY`(core/config).
- 원장(`ledger_entries`)은 append-only. 잔액 = 적립 합(`BALANCE_CREDIT_TYPES`) −
  차감 합(`BALANCE_DEBIT_TYPES`: WITHDRAWAL·CREDIT_SPENT).
- `package_id`·user_id들은 타 스포크 논리 참조(DB FK 없음). 패키지 제목은 표시용 스냅샷
  (이력 보존 — 3NF 허용 예외).
- 예정: admin 분쟁 중재.
  (인출·납품물 업로드·합의 취소·크레딧 재결제·장바구니는 2026-08-11 구축 완료)

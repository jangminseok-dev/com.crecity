# CLAUDE.md — order (스포크)

주문 상태머신 · 에스크로/잔액 원장(돈의 장부 — BOUNDARIES §3). PG 접점은 payment 앱(예정) 몫.

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| bookkeeper (myself) | `GET /order/myself` | 자기소개 |
| order_placement | (HTTP 없음 — 결제 경유 전용) | 주문 생성 — payment 승인 후 허브 `OrderPlacementPort`(order 구현 `PaidOrderPlacementGateway`)로만 호출된다. 커스텀 오퍼 주문(`place_custom`)은 `CustomOfferPort`로 가격·당사자를 해석하며 package_id가 NULL. 금액·수수료율(§7-4)·패키지 제목 스냅샷, 72h 수락 마감, 에스크로 예치 기입. 결제 금액과 현재 계산 불일치 시 생성 거부(None) |
| order_progress | `POST /order/orders/{id}/accept·reject·submit·request-revision·approve` | 상태 전이 — 규칙·행위자 검증은 도메인 `Order`가 강제(403/409). 거절→크레딧 환불, 승인→적립+수수료 확정 |
| order_lookup | `GET /order/orders` · `GET /order/orders/{id}` | 내 주문 목록(최신순)·상세 — **당사자만(403)** |
| balance_lookup | `GET /order/balance` | 내 잔액 — 원장 적립성 기입 합산 |
| deadline_sweep | (HTTP 없음) | 72h 만료 스캔 — `scripts/order_deadline_sweep.py`를 cron이 주기 실행. 수락 만료→환불, 검토 만료→자동 승인 |

## 도메인 규칙 (BOUNDARIES §4 · collabstr §3.8)

```
PENDING_ACCEPT ──수락──▶ IN_PROGRESS ──제출──▶ IN_REVIEW ──승인/72h──▶ COMPLETED
      │                                     │
      ├─ 거절/72h 만료 ─▶ REFUNDED           └─ 수정 요청 ─▶ IN_PROGRESS (무제한)
```

- 상태 전이·수수료 계산은 **순수 도메인**(`Order`) — 정수 원 단위 내림, 부동소수 금지.
- 브랜드 결제 총액 = 가격 + 브랜드 수수료(예치액) · 크리에이터 적립 = 가격 − 크리에이터 수수료.
  요율은 `core/config.py`(`ORDER_*_FEE_PERCENT`, 초기 10/10) — 주문 생성 시점 스냅샷.
- **전이 + 원장 기입 + Outbox 이벤트 = 단일 트랜잭션**(`OrderRepository.create/save_transition`의
  `events` 인자 — BOUNDARIES §1). 이벤트는 `app/events.py`의 `order_event`로 만든다
  (order.placed/accepted/rejected/submitted/revision_requested/completed — notification이 소비).
- 원장(`ledger_entries`)은 append-only. 잔액 = 적립성 기입 합(`BALANCE_CREDIT_TYPES`).
- `package_id`·user_id들은 타 스포크 논리 참조(DB FK 없음). 패키지 제목은 표시용 스냅샷
  (이력 보존 — 3NF 허용 예외).
- 예정: 결제(payment 연동 후 주문 생성 앞단에) · 장바구니 · 양측 합의 취소(CANCELLED 전이) ·
  크레딧 사용·인출(차감성 기입 유형) · 납품물 파일 업로드.

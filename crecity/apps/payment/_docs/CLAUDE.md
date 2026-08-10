# CLAUDE.md — payment (스포크)

외부 결제 접점 전용 — 돈이 시스템 밖과 만나는 지점만 담당(BOUNDARIES §3).
원장은 order 소유이며 payment는 **PG 승인 기록(payment_intents)**만 가진다.
PG는 **토스페이먼츠**(§7-3 확정) — `PaymentGateway` 포트 뒤에 격리(교체 가능, 멀티 PG 추상화 기각).

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| paymaster (myself) | `GET /payment/myself` | 자기소개 |
| checkout_preparation | `POST /payment/checkouts` | 결제 준비 — **브랜드만(403)**. 서버가 결제 총액(가격+수수료) 확정·intent 기록, 결제창 파라미터(pg_order_id·amount·client_key) 응답 |
| payment_confirmation | `POST /payment/confirm` | 토스 승인 → 허브 `OrderPlacementPort`로 주문 생성. 금액 대조 필수(불일치 400), 승인 후 주문 생성 실패 시 **PG 취소 보정**(§3) 후 502 |

## 결제 흐름 (§3)

```
프론트: POST /payment/checkouts → 토스 결제창(SDK v2) → successUrl 리다이렉트
백엔드: POST /payment/confirm → ① intent 검증(소유·상태·금액) → ② 토스 승인
        → ③ 주문 생성+예치(order 원자적, 허브 계약) → 실패 시 토스 취소 보정
```

- intent 상태: READY → CONFIRMED / FAILED(사유 기록 — 보정 실패는 운영 개입 신호).
- 키: `.env` `TOSS_CLIENT_KEY`(공개, 결제창)·`TOSS_SECRET_KEY`(서버 전용) — 미설정이면
  서버는 뜨되 결제만 실패. 테스트 키는 developers.tosspayments.com에서 발급.
- **직접 주문 API는 제거됨** — 주문 생성은 결제 승인 경유(허브 계약)뿐이다.
- 예정: 크리에이터 인출(pay-out — order 잔액 차감 예약과 2단계) · 원천징수 3.3% · 지급명세서 ·
  웹훅(가상계좌 등 비동기 수단 도입 시).

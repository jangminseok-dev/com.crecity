# CLAUDE.md — order (스포크)

주문 상태머신 · 에스크로/잔액 원장(돈의 장부 — BOUNDARIES §3). PG 접점은 payment 앱(예정) 몫.

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| bookkeeper (myself) | `GET /order/myself` | 자기소개 |
| order_placement | (HTTP 없음 — 결제 경유 전용) | 주문 생성 — payment 승인 후 허브 `OrderPlacementPort`(order 구현 `PaidOrderPlacementGateway`)로만 호출된다. 커스텀 오퍼 주문(`place_custom`)은 `CustomOfferPort`로, 캠페인 지원 수락 주문(`place_application`)은 `CampaignApplicationPort`로 가격·당사자를 해석하며 package_id가 NULL. 금액·수수료율(§7-4)·패키지 제목 스냅샷, 72h 수락 마감, 에스크로 예치 기입. 결제 금액과 현재 계산 불일치 시 생성 거부(None). 크레딧 사용분(`credit_used_krw`)은 advisory lock 잔액 재검증 + CREDIT_SPENT 기입을 주문 생성과 단일 트랜잭션으로 — 부족 시 생성 거부. 장바구니(`place_cart`, §3.8)는 주문 N건+예치 N건을 `create_many` **단일 트랜잭션**으로 — 불가 패키지·크레딧 부족 시 전체 거부(부분 생성 없음) |
| order_progress | `POST /order/orders/{id}/accept·reject·submit-draft·approve-draft·submit·request-revision·approve` | 상태 전이 — 규칙·행위자 검증은 도메인 `Order`가 강제(403/409). 거절→크레딧 환불, 승인→적립+수수료 확정. **초안 검토(갭 #85)는 선택 단계**: IN_PROGRESS→초안 제출(납품물 ≥1 전제)→DRAFT_REVIEW(72h, 무응답 자동 컨펌)→컨펌·수정 요청→IN_PROGRESS. 컨펌 표식(`draft_approved`) 후 초안 재제출 409. 수정 요청은 초안·최종 검토가 **같은 한도(revision_limit) 공유**(스냅샷 계약 조건 의미 보존). 취소·분쟁·금액 변경도 DRAFT_REVIEW에서 허용 |
| deliverable_submission | `POST /order/orders/{id}/deliverables/files·links` · `GET /order/orders/{id}/deliverables` | 납품물(파일·링크) — 등록은 **IN_PROGRESS의 크리에이터만**(도메인 `ensure_can_attach_deliverable`), 열람은 당사자만(403). append-only(분쟁 근거 보존), 파일은 `/uploads/deliverables/` 로컬 저장(이미지·영상·PDF·ZIP, 100MB). 링크는 게시물 본문(`caption`, 3000자, 선택)을 함께 받아 **광고 표기 자동 검수**(갭 #17) |
| order_cancellation | `POST /order/orders/{id}/cancel-request·cancel-consent·cancel-decline` | 양측 합의 취소 — 요청은 IN_PROGRESS·IN_REVIEW의 당사자 누구나(중복 409), 동의·거부는 **상대방만**(403). 동의 시 CANCELLED + 브랜드 전액 크레딧 환불(단일 트랜잭션). `orders.cancel_requested_by`가 대기 상태 표현 |
| order_adjustment | `POST·GET /order/orders/{id}/adjustments` · `POST /order/adjustments/{id}/decline` | 진행 중 금액 변경(§3.8·§6, 갭 #31) — 요청은 **IN_PROGRESS·IN_REVIEW의 크리에이터만**(대기 중 중복 409), 거절은 브랜드만. **수락은 추가 결제**(payment `/checkouts/adjustment` → 허브 `OrderAdjustmentPort`로 주문 증액+증가분 예치 단일 트랜잭션). 감액은 미지원(합의 취소로) |
| dispute | `POST·GET /order/orders/{id}/disputes` | 분쟁 신고·이력(§3.8 지원팀 중재, 갭 #4) — 신고는 **IN_PROGRESS·IN_REVIEW의 당사자**(사유 10~2000자, 대기 중 분쟁이 있으면 409), 열람은 당사자만. **판정은 admin**(허브 `DisputeResolutionPort`) — 환불(CANCELLED+전액 크레딧)·지급(COMPLETED+적립)·기각(주문 유지). 대기 분쟁이 있으면 `find_expired`가 그 주문을 건너뛴다(자동 승인 보류) |
| revision_lookup | `GET /order/orders/{id}/revisions` | 수정 요청 이력(갭 #84) — **당사자만(403)**, 요청순. 기록은 `request-revision`이 코멘트(5~2000자 필수)를 `save_transition(revision_comment=…)`으로 전이와 **단일 트랜잭션** 저장(`order_revision_requests`, append-only). `requested_in`(전이 전 상태)이 초안/최종 검토를 구분한다. 횟수 정본은 `orders.revisions_used`(도입 이전 포함) — 이 테이블은 본문 이력 |
| order_lookup | `GET /order/orders` · `GET /order/orders/{id}` | 내 주문 목록(최신순)·상세 — **당사자만(403)**. 응답에 **조회자 기준 거래 상대**(`counterpart_name`·`counterpart_slug`, 갭 #63)를 붙인다 — 허브 `CreatorRefPort`·`UserDirectoryPort` 경유, 상대 id를 모아 한 번씩만 조회(N+1 회피). 참조가 끊겨도 조회는 성공 |
| party_stats | (HTTP 없음) | 당사자 거래 이력 집계(갭 #65·#66) — `OrderRepository.get_party_stats(user_id, as_brand)`가 상태별 건수·수정 누적을 한 쿼리로 센다. 주문 조회가 상대 이력을 붙이고, 허브 `CreatorTradeStatsPort`(order 구현)가 creator에 실적을 넘긴다. 시간 지표의 원천은 전이 이력(아래 행) |
| status_transition_history | (HTTP 없음) | 주문 상태 전이 이력(갭 #79) — `order_status_transitions`(append-only, from·to·occurred_at). **`save_transition`이 저장 직전 DB 상태를 읽어 from으로 기록**한다(엔티티의 옛 상태보다 동시성에서 정확) — 전이 UPDATE·원장·이벤트와 단일 커밋. 상태가 안 바뀌는 저장(취소 요청·거부)은 기록하지 않는다. 최초 상태 행은 만들지 않는다 — 시작 시각은 `orders.created_at`이 정본(복사 시 3NF 위반). 도입(2026-08-18) 이전 주문은 이력 없음(소급 불가). 응답 지표(갭 #80)의 원천 |
| response_stats | (HTTP 없음) | 응답 지표(갭 #80) — `get_creator_response_stats`(PG 전용, 포트 미승격 — 소비자가 허브 게이트웨이뿐)가 수락 대기 이탈 전이를 집계(평균 수락 소요·응답/만료 건수). **빠른 응답 배지 판정은 도메인 순수 함수** `response_speed.py`(표본 `ORDER_FAST_RESPONSE_MIN_SAMPLES` 이상 + 평균 `ORDER_FAST_RESPONSE_HOURS` 이내 + 만료 0건 — 기준값은 core/config 소유). `CreatorTradeStatsPort` 게이트웨이가 거래 실적(#66)에 얹어 creator로 넘긴다 |
| completed_price | (HTTP 없음) | 실거래가 제공(갭 #89) — 허브 `CompletedOrderPricePort` 구현(`OrderCompletedPriceGateway`): COMPLETED·패키지 있는 주문의 (package_id, amount)를 최신 1만 건 상한으로 넘긴다. 분류·집계는 creator 몫(카테고리·플랫폼은 creator 소유 — 스포크 경계) |
| fee_policy | `GET /order/fee-policy` | **공개** 수수료·마감 정책(갭 #62) — 요율·원천징수 퍼밀·응답 마감을 그대로 내려준다. 화면이 숫자를 하드코딩하지 않게 하는 것이 목적(설정이 바뀌면 화면도 따라온다). I/O가 없어 유스케이스는 `def` |
| balance_lookup | `GET /order/balance` | 내 잔액 = 적립성 기입 합 − 차감성 기입 합 |
| monthly_report | `GET /order/reports/{year}` | 월별 수익·지출 리포트(갭 #90) — **항상 본인 기준**. 원장 기입을 (월, entry_type)로 합산해 그대로 내려준다(`LedgerRepository.monthly_summary`) — **주문 표가 아니라 원장을 집계**해야 환불·인출·복원이 다 잡힌다. 계정 유형별 표 구성·CSV 생성은 화면 몫(`monthly-report.tsx` — 크리에이터: 수익 적립·인출·복원 / 브랜드: 예치·크레딧 사용·환불 크레딧). 원천징수 세액은 지급명세서(#2)가 정본 |
| withdrawal_request | `POST/GET /order/withdrawals` | 크리에이터 적립금 인출 — 요청 시 잔액 재검증+차감 기입(WITHDRAWAL)을 advisory lock 단일 트랜잭션으로(과인출 차단), 원천징수 3.3% 세액·실지급액 스냅샷. 운영 처리(완료/실패·복원)는 허브 `WithdrawalSettlementPort`(order 구현 게이트웨이)로 admin이 수행. **처리 결과는 크리에이터에게 알린다**(갭 #74) — `withdrawal.paid`(실지급액)·`withdrawal.failed`(복원 금액)를 상태 갱신·복원 기입과 **단일 트랜잭션**으로 적재(`save_settlement`의 `events` 인자, 빌더는 `app/withdrawal_events.py`). 돈이 오가는 사건이라 공백이 크고, 실패 시 잔액 복원도 조용히 일어난다 |
| payout_statement | `GET /order/withdrawals/statements/{year}` | 연간 지급명세서(갭 #2) — **항상 본인 기준**(남의 명세 조회 불가). 지급 완료(PAID)된 인출을 지급일(`settled_at`) 연도로 집계 + 건별 내역. 새 테이블 없음(집계는 `AnnualPayout` VO). 운영자용 크리에이터별 집계는 admin `GET /admin/withdrawals/annual-summary/{year}` |
| deadline_sweep | (HTTP 없음) | 72h 만료 스캔 — `scripts/order_deadline_sweep.py`를 cron이 주기 실행. 수락 만료→환불, 검토 만료→자동 승인. **만료 전 임박 알림**(갭 #76)도 같은 스캔이 보낸다 — `ORDER_DEADLINE_WARNING_HOURS`(12h) 안으로 들어오면 움직여야 하는 쪽에 1회. 중복은 `deadline_warned_at` 표식으로 막고 **표식+이벤트를 단일 트랜잭션**으로 남긴다(`record_deadline_warnings`). 제출로 마감이 재설정되면 표식도 비워진다 |

## 도메인 규칙 (BOUNDARIES §4 · collabstr §3.8)

```
PENDING_ACCEPT ──수락──▶ IN_PROGRESS ──제출──▶ IN_REVIEW ──승인/72h──▶ COMPLETED
      │                    │    ▲                │
      │           초안 제출│    │컨펌/72h·수정 요청 └─ 수정 요청 ─▶ IN_PROGRESS (revision_limit까지)
      │                    ▼    │
      │                 DRAFT_REVIEW  (선택 — 게시 전 초안 검토, 갭 #85)
      └─ 거절/72h 만료 ─▶ REFUNDED

IN_PROGRESS·DRAFT_REVIEW·IN_REVIEW ──취소 요청→상대 동의──▶ CANCELLED (브랜드 전액 크레딧 환불)
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
- **분쟁 중재(갭 #4)**: 판정은 **전액 단위**만 — 부분 배분은 지원하지 않는다(원장·도메인
  복잡도 대비 실익이 낮아 명시적 제외). 판정 = 분쟁 갱신 + 주문 전이 + 원장 기입 + 이벤트
  단일 커밋(`DisputeRepository.resolve`가 같은 세션의 `OrderPgRepository.save_transition`을
  호출해 원자성 확보). 기각은 주문을 건드리지 않는다.

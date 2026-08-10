# CLAUDE.md — chat (스포크)

주문 전 협상 메시징 — 대화·메시지는 분쟁 근거로 보존된다(수정·삭제 없음, BOUNDARIES).
실시간은 웹소켓 대신 **주기 폴링**(프론트 5~10초) — 단순·크래시 안전.

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| courier (myself) | `GET /chat/myself` | 자기소개 |
| conversation_opening | `POST /chat/conversations` | **브랜드만(403)** 크리에이터에게 문의 시작 — 쌍당 1개(있으면 재사용, DB 복합 unique) |
| conversation_listing | `GET /chat/conversations` · `/{id}` | 내 대화 목록(최근 메시지순·미리보기)·상세 — **참여자만(403)** |
| messaging | `POST·GET /chat/conversations/{id}/messages` | 전송(빈 본문 422)·조회(오래된 순 최근 100) — **참여자만(403)** |
| offer_management | `POST·GET /chat/conversations/{id}/offers` | 커스텀 오퍼 — 제안은 **해당 대화의 크리에이터만(403)**, 열람은 참여자만. 제목 1~100자·가격 양수(422), PENDING→PAID는 결제 완료 시 허브 경유로만 전이 |

- 엔티티: `Conversation`(참여자 검증 `ensure_participant`·상대 판정) · `Message`(append-only) ·
  `CustomOffer`(+`OfferStatus`, `is_payable`). 오퍼 수신자·제안자는 대화방이 알고 있어
  중복 저장하지 않는다(3NF). `order_id`는 논리 참조.
- 허브 `CustomOfferPort` 구현(`CustomOfferGateway`) 제공 — payment(결제 준비·PAID 처리)와
  order(커스텀 주문 가격·당사자 해석)가 소비한다.
- 상대 표시는 스냅샷 없이 허브로 실시간 해석 — 크리에이터면 `CreatorRefPort`(이름·슬러그),
  브랜드면 `UserDirectoryPort`(이름, §5 "회원 디렉토리 조회" 실현 — auth 구현).
- 예정: 안 읽음 표시 · 팀 초대 · 신고.

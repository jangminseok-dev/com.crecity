# CLAUDE.md — chat (스포크)

주문 전 협상 메시징 — 대화·메시지는 분쟁 근거로 보존된다(수정·삭제 없음, BOUNDARIES).
실시간은 웹소켓 대신 **주기 폴링**(프론트 5~10초) — 단순·크래시 안전.

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| courier (myself) | `GET /chat/myself` | 자기소개 |
| conversation_opening | `POST /chat/conversations` | **브랜드만(403)** 크리에이터에게 문의 시작 — 쌍당 1개(있으면 재사용, DB 복합 unique) |
| conversation_listing | `GET /chat/conversations` · `/{id}` · `POST /chat/conversations/{id}/read` | 내 대화 목록(최근 메시지순·미리보기)·상세 — **참여자만(403)** |
| messaging | `POST·GET /chat/conversations/{id}/messages` | 전송(빈 본문 422)·조회(오래된 순 최근 100) — **참여자만(403)** |
| offer_management | `POST·GET /chat/conversations/{id}/offers` | 커스텀 오퍼 — 제안은 **해당 대화의 크리에이터만(403)**, 열람은 참여자만. 제목 1~100자·가격 양수(422), PENDING→PAID는 결제 완료 시 허브 경유로만 전이 |

- 엔티티: `Conversation`(참여자 검증 `ensure_participant`·상대 판정) · `Message`(append-only) ·
  `CustomOffer`(+`OfferStatus`, `is_payable`). 오퍼 수신자·제안자는 대화방이 알고 있어
  중복 저장하지 않는다(3NF). `order_id`는 논리 참조.
- 허브 `CustomOfferPort` 구현(`CustomOfferGateway`) 제공 — payment(결제 준비·PAID 처리)와
  order(커스텀 주문 가격·당사자 해석)가 소비한다.
- 상대 표시는 스냅샷 없이 허브로 실시간 해석 — 크리에이터면 `CreatorRefPort`(이름·슬러그),
  브랜드면 `UserDirectoryPort`(이름, §5 "회원 디렉토리 조회" 실현 — auth 구현).
- **안 읽음 표시(갭 #35)**: `conversation_reads`(대화방×참여자 조인 테이블, 3NF)의
  `last_read_at` 이후 도착한 **상대** 메시지를 센다 — 읽음 기록이 없으면 전부 안 읽음.
- **새 메시지 알림(갭 #72)**: 텍스트·사진 전송이 `chat.message_received` Outbox 이벤트를
  메시지 저장과 **같은 트랜잭션**으로 남긴다(`MessageRepository.create`의 `events` 인자).
  조립은 `app/message_notifications.py` 한 곳 — 두 인터랙터에 복제하면 규칙이 갈라진다.
  **상대가 이미 안 읽은 메시지를 갖고 있으면 보내지 않는다** — 연속 전송마다 알리면
  알림함이 도배된다(상대가 한 번 읽으면 다음 메시지에 다시 간다). 보낸 사람 이름은
  스냅샷 없이 허브로 해석(크리에이터=`CreatorRefPort`, 브랜드=`UserDirectoryPort`).
- 예정: 팀 초대(30번 — 팀 워크스페이스와 함께) · 신고.

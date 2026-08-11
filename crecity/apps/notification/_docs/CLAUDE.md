# CLAUDE.md — notification (스포크)

인앱 알림 · 허브 Outbox의 첫 소비자(BOUNDARIES §1). 알림톡·이메일 발송은 예정.

## 현재 슬라이스

| 슬라이스 | 엔드포인트 | 설명 |
|---|---|---|
| bellman (myself) | `GET /notification/myself` | 자기소개 |
| notification_listing | `GET /notification/notifications` · `POST /notification/notifications/{id}/read` · `POST /notification/notifications/read-all` | 내 알림 목록(최신순 50건)+안 읽음 개수 · 모두 읽음(204) — 로그인 필수 |
| outbox_relay | (HTTP 없음) | `scripts/notification_outbox_worker.py`를 cron이 주기 실행 — 허브 `outbox_events` 미발행분을 읽어 인앱 알림으로 변환하고 발행 마킹까지 **단일 커밋**(중복 방지) |

## 이벤트 → 알림 매핑 (`OutboxRelayInteractor._to_drafts`)

| 이벤트 | 수신자 | 링크 |
|---|---|---|
| order.placed | 크리에이터 | /dashboard/orders/{id} |
| order.accepted · rejected · submitted | 브랜드 | /dashboard/orders/{id} |
| order.revision_requested · completed(적립액 표기) | 크리에이터 | /dashboard/orders/{id} |
| order.cancel_requested | 요청자의 상대방(payload `requested_by`로 판정) | /dashboard/orders/{id} |
| order.cancelled | 브랜드(환불 안내)+크리에이터 양측 | /dashboard/orders/{id} |
| order.cancel_declined | 요청자(payload `requested_by`) | /dashboard/orders/{id} |
| profile.approved · rejected | 크리에이터 | /dashboard/profile |
| (모르는 유형) | 알림 없이 발행 마킹만 — 재처리 루프 방지 | — |

- 발행 측: order 리포지토리(`create`/`save_transition`의 `events` 인자)와 creator 심사
  게이트웨이가 자기 트랜잭션에 `enqueue_events`로 함께 커밋한다(상태+이벤트 원자성).
- `user_id`·payload 속 id들은 타 스포크 논리 참조(DB FK 없음). 크래시 안전: 마킹 전에
  죽으면 다음 주기에 재처리된다.
- 프론트: 헤더 🔔 안 읽음 뱃지(30초 폴링) + `/notifications` 페이지(진입 시 모두 읽음).
- 개별 읽음(갭 #34)은 본인 알림만 갱신한다(남의 알림 id를 넣으면 404).
- 예정: 알림톡·이메일 발송(15번 — 카카오 비즈 전환과 함께).

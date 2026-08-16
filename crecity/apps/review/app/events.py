"""리뷰 도메인 이벤트 빌더(갭 #75).

이벤트는 리뷰 저장과 같은 트랜잭션에 적재된다(리포지토리가 담당, BOUNDARIES §1).
리뷰 id는 저장 후에야 정해지므로 payload에 담지 않는다 — 링크는 프로필로 충분하다.
"""

from __future__ import annotations

from hub.app.dtos.outbox_event_dto import OutboxEvent


def review_received_event(creator_user_id: int, creator_slug: str) -> OutboxEvent:
    return OutboxEvent(
        event_type="review.received",
        payload={"creator_user_id": creator_user_id, "creator_slug": creator_slug},
    )

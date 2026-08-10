"""주문 도메인 이벤트 빌더 — placement·progress·sweep 슬라이스가 공유한다.

이벤트는 상태 변경과 같은 트랜잭션에 적재된다(리포지토리가 담당, BOUNDARIES §1).
소비자(notification)가 payload로 수신자·문구를 결정한다.
"""

from __future__ import annotations

from hub.app.dtos.outbox_event_dto import OutboxEvent
from order.domain.entities.order_entity import Order


def order_event(event_type: str, order: Order, **extra: int | str) -> OutboxEvent:
    return OutboxEvent(
        event_type=event_type,
        payload={
            "order_id": order.id,
            "package_title": order.package_title,
            "brand_user_id": order.brand_user_id,
            "creator_user_id": order.creator_user_id,
            **extra,
        },
    )

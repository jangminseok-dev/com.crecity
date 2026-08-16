"""채팅 도메인 이벤트 빌더 — 메시지 저장과 같은 트랜잭션에 적재된다(BOUNDARIES §1).

소비자(notification)가 payload로 수신자·문구를 결정한다.
"""

from __future__ import annotations

from hub.app.dtos.outbox_event_dto import OutboxEvent


def message_received_event(
    conversation_id: int, recipient_user_id: int, sender_name: str
) -> OutboxEvent:
    """새 메시지 알림(갭 #72).

    sender_name은 발행 시점 스냅샷이다 — 알림 문구는 그때 사실을 그대로 남긴다.
    """
    return OutboxEvent(
        event_type="chat.message_received",
        payload={
            "conversation_id": conversation_id,
            "recipient_user_id": recipient_user_id,
            "sender_name": sender_name,
        },
    )

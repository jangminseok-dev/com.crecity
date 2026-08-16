"""새 메시지 알림 조립(갭 #72) — 텍스트·사진 전송이 함께 쓴다.

두 인터랙터에 복제하면 한쪽만 고쳐져 알림 규칙이 갈라진다.
"""

from __future__ import annotations

from chat.app.events import message_received_event
from chat.app.ports.output.message_repository import MessageRepository
from chat.domain.entities.conversation_entity import Conversation
from hub.app.dtos.outbox_event_dto import OutboxEvent
from hub.app.ports.output.creator_ref_port import CreatorRefPort
from hub.app.ports.output.user_directory_port import UserDirectoryPort


async def build_message_events(
    conversation: Conversation,
    sender_user_id: int,
    messages: MessageRepository,
    creators: CreatorRefPort,
    users: UserDirectoryPort,
) -> list[OutboxEvent] | None:
    """**상대가 이미 안 읽은 메시지를 갖고 있으면 보내지 않는다.**

    연속 전송마다 알리면 알림함이 도배된다. 상대가 한 번 읽고 나면 다시 알림이 간다.
    """
    recipient = conversation.counterpart_of(sender_user_id)
    unread = await messages.unread_counts(recipient, [conversation.id])
    if unread.get(conversation.id, 0) > 0:
        return None

    if sender_user_id == conversation.creator_user_id:
        creator = await creators.get_creator_by_user_id(sender_user_id)
        sender_name = creator.name if creator else "크리에이터"
    else:
        user = await users.get_user(sender_user_id)
        sender_name = user.name if user else "브랜드"

    return [
        message_received_event(
            conversation_id=conversation.id,
            recipient_user_id=recipient,
            sender_name=sender_name,
        )
    ]

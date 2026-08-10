from chat.adapter.outbound.orm.conversation_orm import ConversationOrm, MessageOrm
from chat.domain.entities.conversation_entity import Conversation, Message


class ConversationMapper:
    """Conversation/Message ORM(영속성) ↔ 도메인 변환을 담당한다."""

    @staticmethod
    def to_entity(orm: ConversationOrm) -> Conversation:
        return Conversation(
            id=orm.id,
            brand_user_id=orm.brand_user_id,
            creator_user_id=orm.creator_user_id,
            created_at=orm.created_at,
        )

    @staticmethod
    def message_to_entity(orm: MessageOrm) -> Message:
        return Message(
            id=orm.id,
            conversation_id=orm.conversation_id,
            sender_user_id=orm.sender_user_id,
            body=orm.body,
            created_at=orm.created_at,
        )

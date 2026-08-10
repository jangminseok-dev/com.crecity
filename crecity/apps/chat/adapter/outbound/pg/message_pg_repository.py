from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from chat.adapter.outbound.mappers.conversation_mapper import ConversationMapper
from chat.adapter.outbound.orm.conversation_orm import MessageOrm
from chat.app.ports.output.message_repository import MessageRepository
from chat.domain.entities.conversation_entity import Message


class MessagePgRepository(MessageRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, conversation_id: int, sender_user_id: int, body: str) -> Message:
        result = await self._session.execute(
            insert(MessageOrm)
            .values(conversation_id=conversation_id, sender_user_id=sender_user_id, body=body)
            .returning(MessageOrm)
        )
        await self._session.commit()
        return ConversationMapper.message_to_entity(result.scalar_one())

    async def list_by_conversation(self, conversation_id: int, limit: int) -> list[Message]:
        # 최근 limit개를 골라 오래된 순으로 돌려준다
        result = await self._session.execute(
            select(MessageOrm)
            .where(MessageOrm.conversation_id == conversation_id)
            .order_by(MessageOrm.created_at.desc(), MessageOrm.id.desc())
            .limit(limit)
        )
        messages = [ConversationMapper.message_to_entity(orm) for orm in result.scalars()]
        return list(reversed(messages))

    async def last_by_conversation(self, conversation_id: int) -> Message | None:
        result = await self._session.execute(
            select(MessageOrm)
            .where(MessageOrm.conversation_id == conversation_id)
            .order_by(MessageOrm.created_at.desc(), MessageOrm.id.desc())
            .limit(1)
        )
        orm = result.scalar_one_or_none()
        return ConversationMapper.message_to_entity(orm) if orm is not None else None

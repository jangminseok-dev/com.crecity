from sqlalchemy import func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from chat.adapter.outbound.mappers.conversation_mapper import ConversationMapper
from chat.adapter.outbound.orm.conversation_orm import ConversationReadOrm, MessageOrm
from chat.app.ports.output.message_repository import MessageRepository
from chat.domain.entities.conversation_entity import Message


class MessagePgRepository(MessageRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        conversation_id: int,
        sender_user_id: int,
        body: str,
        image_file_name: str | None = None,
    ) -> Message:
        result = await self._session.execute(
            insert(MessageOrm)
            .values(
                conversation_id=conversation_id,
                sender_user_id=sender_user_id,
                body=body,
                image_file_name=image_file_name,
            )
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

    async def unread_counts(self, user_id: int, conversation_ids: list[int]) -> dict[int, int]:
        if not conversation_ids:
            return {}
        # 읽음 기록이 없으면 대화방의 모든 상대 메시지가 안 읽음이다(LEFT JOIN + NULL 처리)
        reads = (
            select(ConversationReadOrm.conversation_id, ConversationReadOrm.last_read_at)
            .where(ConversationReadOrm.user_id == user_id)
            .subquery()
        )
        result = await self._session.execute(
            select(MessageOrm.conversation_id, func.count())
            .select_from(MessageOrm)
            .outerjoin(reads, reads.c.conversation_id == MessageOrm.conversation_id)
            .where(
                MessageOrm.conversation_id.in_(conversation_ids),
                MessageOrm.sender_user_id != user_id,  # 내가 보낸 건 세지 않는다
                (reads.c.last_read_at.is_(None)) | (MessageOrm.created_at > reads.c.last_read_at),
            )
            .group_by(MessageOrm.conversation_id)
        )
        return {conversation_id: int(count) for conversation_id, count in result}

    async def mark_read(self, conversation_id: int, user_id: int) -> None:
        updated = await self._session.execute(
            update(ConversationReadOrm)
            .where(
                ConversationReadOrm.conversation_id == conversation_id,
                ConversationReadOrm.user_id == user_id,
            )
            .values(last_read_at=func.now())
        )
        if updated.rowcount == 0:
            await self._session.execute(
                insert(ConversationReadOrm).values(
                    conversation_id=conversation_id, user_id=user_id
                )
            )
        await self._session.commit()

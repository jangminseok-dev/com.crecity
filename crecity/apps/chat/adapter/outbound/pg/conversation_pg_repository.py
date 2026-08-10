from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from chat.adapter.outbound.mappers.conversation_mapper import ConversationMapper
from chat.adapter.outbound.orm.conversation_orm import ConversationOrm
from chat.app.ports.output.conversation_repository import ConversationRepository
from chat.domain.entities.conversation_entity import Conversation


class ConversationPgRepository(ConversationRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, brand_user_id: int, creator_user_id: int) -> Conversation:
        result = await self._session.execute(
            insert(ConversationOrm)
            .values(brand_user_id=brand_user_id, creator_user_id=creator_user_id)
            .returning(ConversationOrm)
        )
        await self._session.commit()
        return ConversationMapper.to_entity(result.scalar_one())

    async def find_by_pair(self, brand_user_id: int, creator_user_id: int) -> Conversation | None:
        result = await self._session.execute(
            select(ConversationOrm).where(
                ConversationOrm.brand_user_id == brand_user_id,
                ConversationOrm.creator_user_id == creator_user_id,
            )
        )
        orm = result.scalar_one_or_none()
        return ConversationMapper.to_entity(orm) if orm is not None else None

    async def find_by_id(self, conversation_id: int) -> Conversation | None:
        result = await self._session.execute(
            select(ConversationOrm).where(ConversationOrm.id == conversation_id)
        )
        orm = result.scalar_one_or_none()
        return ConversationMapper.to_entity(orm) if orm is not None else None

    async def list_by_participant(self, user_id: int) -> list[Conversation]:
        result = await self._session.execute(
            select(ConversationOrm).where(
                (ConversationOrm.brand_user_id == user_id)
                | (ConversationOrm.creator_user_id == user_id)
            )
        )
        return [ConversationMapper.to_entity(orm) for orm in result.scalars()]

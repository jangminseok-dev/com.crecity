from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from chat.adapter.outbound.mappers.custom_offer_mapper import to_entity
from chat.adapter.outbound.orm.custom_offer_orm import CustomOfferOrm
from chat.app.ports.output.custom_offer_repository import CustomOfferRepository
from chat.domain.entities.custom_offer_entity import CustomOffer, OfferStatus


class CustomOfferPgRepository(CustomOfferRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        conversation_id: int,
        title: str,
        price_krw: int,
        revision_limit: int,
        usage_rights: str,
    ) -> CustomOffer:
        orm = CustomOfferOrm(
            conversation_id=conversation_id,
            title=title,
            price_krw=price_krw,
            revision_limit=revision_limit,
            usage_rights=usage_rights,
            status=OfferStatus.PENDING.value,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return to_entity(orm)

    async def find_by_id(self, offer_id: int) -> CustomOffer | None:
        orm = await self._session.get(CustomOfferOrm, offer_id)
        return to_entity(orm) if orm is not None else None

    async def list_by_conversation(self, conversation_id: int) -> list[CustomOffer]:
        stmt = (
            select(CustomOfferOrm)
            .where(CustomOfferOrm.conversation_id == conversation_id)
            .order_by(CustomOfferOrm.id)
        )
        return [to_entity(orm) for orm in (await self._session.scalars(stmt)).all()]

    async def mark_paid(self, offer_id: int, order_id: int) -> None:
        await self._session.execute(
            update(CustomOfferOrm)
            .where(CustomOfferOrm.id == offer_id)
            .values(status=OfferStatus.PAID.value, order_id=order_id)
        )
        await self._session.commit()

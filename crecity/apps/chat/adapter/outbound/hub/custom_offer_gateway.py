from __future__ import annotations

from chat.adapter.outbound.pg.conversation_pg_repository import ConversationPgRepository
from chat.adapter.outbound.pg.custom_offer_pg_repository import CustomOfferPgRepository
from core.database import session_scope
from hub.app.dtos.custom_offer_dto import CustomOfferSummary
from hub.app.ports.output.custom_offer_port import CustomOfferPort


class CustomOfferGateway(CustomOfferPort):
    """허브 CustomOfferPort 계약의 chat 구현 — main.py가 조립한다."""

    async def get_payable_offer(self, offer_id: int) -> CustomOfferSummary | None:
        async with session_scope() as session:
            offer = await CustomOfferPgRepository(session).find_by_id(offer_id)
            if offer is None or not offer.is_payable():
                return None
            conversation = await ConversationPgRepository(session).find_by_id(
                offer.conversation_id
            )
        if conversation is None:  # FK가 보장 — 데이터 손상 신호
            return None
        return CustomOfferSummary(
            offer_id=offer.id,
            title=offer.title,
            price_krw=offer.price_krw,
            brand_user_id=conversation.brand_user_id,
            creator_user_id=conversation.creator_user_id,
        )

    async def mark_paid(self, offer_id: int, order_id: int) -> None:
        async with session_scope() as session:
            await CustomOfferPgRepository(session).mark_paid(offer_id, order_id)

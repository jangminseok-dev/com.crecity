from __future__ import annotations

from chat.app.dtos.offer_management_dto import (
    OfferCreationCommand,
    OfferResult,
    OffersQuery,
)
from chat.app.exceptions import ConversationNotFoundError, NotConversationCreatorError
from chat.app.ports.input.offer_management_use_case import OfferManagementUseCase
from chat.app.ports.output.conversation_repository import ConversationRepository
from chat.app.ports.output.custom_offer_repository import CustomOfferRepository
from chat.domain.entities.custom_offer_entity import CustomOffer

# 오퍼 제목·가격 상한 — 제목은 주문 스냅샷(String 100)과 맞추고, 가격은 결제 한도 여유분
_MAX_TITLE_LENGTH = 100
_MAX_PRICE_KRW = 100_000_000


def _to_result(offer: CustomOffer) -> OfferResult:
    return OfferResult(
        id=offer.id,
        conversation_id=offer.conversation_id,
        title=offer.title,
        price_krw=offer.price_krw,
        status=offer.status.value,
        order_id=offer.order_id,
        created_at=offer.created_at,
    )


class OfferManagementInteractor(OfferManagementUseCase):

    def __init__(
        self,
        conversations: ConversationRepository,
        offers: CustomOfferRepository,
    ) -> None:
        self._conversations = conversations
        self._offers = offers

    async def create(self, command: OfferCreationCommand) -> OfferResult:
        conversation = await self._conversations.find_by_id(command.conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(
                f"대화를 찾을 수 없습니다: {command.conversation_id}"
            )
        if conversation.creator_user_id != command.requester_user_id:
            raise NotConversationCreatorError("이 대화의 크리에이터만 오퍼를 보낼 수 있습니다.")
        title = command.title.strip()
        if not title or len(title) > _MAX_TITLE_LENGTH:
            raise ValueError(f"오퍼 제목은 1~{_MAX_TITLE_LENGTH}자여야 합니다.")
        if command.price_krw <= 0 or command.price_krw > _MAX_PRICE_KRW:
            raise ValueError(f"가격은 1원 이상 {_MAX_PRICE_KRW:,}원 이하여야 합니다.")
        offer = await self._offers.create(
            conversation_id=conversation.id, title=title, price_krw=command.price_krw
        )
        return _to_result(offer)

    async def list_for_conversation(self, query: OffersQuery) -> list[OfferResult]:
        conversation = await self._conversations.find_by_id(query.conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"대화를 찾을 수 없습니다: {query.conversation_id}")
        conversation.ensure_participant(query.requester_user_id)
        offers = await self._offers.list_by_conversation(conversation.id)
        return [_to_result(offer) for offer in offers]

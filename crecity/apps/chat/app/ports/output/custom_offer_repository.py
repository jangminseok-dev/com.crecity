from abc import ABC, abstractmethod

from chat.domain.entities.custom_offer_entity import CustomOffer


class CustomOfferRepository(ABC):

    @abstractmethod
    async def create(
        self,
        conversation_id: int,
        title: str,
        price_krw: int,
        revision_limit: int,
        usage_rights: str,
    ) -> CustomOffer: ...

    @abstractmethod
    async def find_by_id(self, offer_id: int) -> CustomOffer | None: ...

    @abstractmethod
    async def list_by_conversation(self, conversation_id: int) -> list[CustomOffer]:
        """등록순 정렬."""

    @abstractmethod
    async def mark_paid(self, offer_id: int, order_id: int) -> None: ...

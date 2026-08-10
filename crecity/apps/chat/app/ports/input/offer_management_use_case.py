from abc import ABC, abstractmethod

from chat.app.dtos.offer_management_dto import (
    OfferCreationCommand,
    OfferResult,
    OffersQuery,
)


class OfferManagementUseCase(ABC):

    @abstractmethod
    async def create(self, command: OfferCreationCommand) -> OfferResult: ...

    @abstractmethod
    async def list_for_conversation(self, query: OffersQuery) -> list[OfferResult]: ...

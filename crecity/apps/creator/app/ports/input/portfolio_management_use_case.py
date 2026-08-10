from abc import ABC, abstractmethod

from creator.app.dtos.portfolio_management_dto import (
    PortfolioItemResult,
    PortfolioListQuery,
    PortfolioRemovalCommand,
    PortfolioUploadCommand,
)


class PortfolioManagementUseCase(ABC):

    @abstractmethod
    async def upload(self, command: PortfolioUploadCommand) -> PortfolioItemResult: ...

    @abstractmethod
    async def remove(self, command: PortfolioRemovalCommand) -> None: ...

    @abstractmethod
    async def list_for_profile(self, query: PortfolioListQuery) -> list[PortfolioItemResult]: ...

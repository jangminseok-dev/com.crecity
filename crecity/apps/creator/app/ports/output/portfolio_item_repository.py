from abc import ABC, abstractmethod

from creator.domain.entities.portfolio_item_entity import PortfolioItem


class PortfolioItemRepository(ABC):

    @abstractmethod
    async def create(self, profile_id: int, file_name: str) -> PortfolioItem: ...

    @abstractmethod
    async def find_by_id(self, item_id: int) -> PortfolioItem | None: ...

    @abstractmethod
    async def list_by_profile_id(self, profile_id: int) -> list[PortfolioItem]:
        """등록순 정렬."""

    @abstractmethod
    async def count_by_profile_id(self, profile_id: int) -> int: ...

    @abstractmethod
    async def delete(self, item_id: int) -> bool:
        """삭제 성공 여부 — 없으면 False."""

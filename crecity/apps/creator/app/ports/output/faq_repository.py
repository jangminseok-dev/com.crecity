from __future__ import annotations

from abc import ABC, abstractmethod

from creator.domain.entities.profile_faq_entity import ProfileFaq


class FaqRepository(ABC):
    """프로필 FAQ 영속성 포트."""

    @abstractmethod
    async def add(self, profile_id: int, question: str, answer: str) -> ProfileFaq: ...

    @abstractmethod
    async def list_by_profile_id(self, profile_id: int) -> list[ProfileFaq]:
        """등록순."""
        ...

    @abstractmethod
    async def count_by_profile_id(self, profile_id: int) -> int: ...

    @abstractmethod
    async def delete(self, profile_id: int, faq_id: int) -> bool:
        """내 프로필의 FAQ만 삭제 — 없으면 False."""
        ...

from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.faq_management_dto import AddFaqCommand, FaqResult, RemoveFaqCommand


class FaqManagementUseCase(ABC):
    """프로필 FAQ(§2.1-9) — 크리에이터가 직접 쓰는 자주 묻는 질문. 열람은 공개."""

    @abstractmethod
    async def add(self, command: AddFaqCommand) -> FaqResult:
        """FAQ 추가.

        Raises:
            ProfileNotFoundError: 내 프로필 없음.
            FaqLimitExceededError: 프로필당 상한 초과.
            ValueError: 질문·답변이 비었거나 너무 김.
        """
        ...

    @abstractmethod
    async def list_mine(self, requester_user_id: int) -> list[FaqResult]:
        """내 FAQ 목록(대시보드).

        Raises:
            ProfileNotFoundError: 내 프로필 없음.
        """
        ...

    @abstractmethod
    async def remove(self, command: RemoveFaqCommand) -> None:
        """FAQ 삭제 — 내 프로필의 FAQ만.

        Raises:
            ProfileNotFoundError: 내 프로필 없음.
            FaqNotFoundError: 없거나 내 것이 아님.
        """
        ...

    @abstractmethod
    async def list_public(self, slug: str) -> list[FaqResult]:
        """프로필 FAQ 목록(공개 — 아코디언).

        Raises:
            ProfileNotFoundError: 프로필 없음.
        """
        ...

from __future__ import annotations

from abc import ABC, abstractmethod

from auth.domain.entities.user_entity import AccountType, User


class UserRepository(ABC):
    """회원 영속성 포트 — 소셜 로그인·토큰 갱신 슬라이스가 공유한다(도메인어 명명 예외)."""

    @abstractmethod
    async def create(self, email: str, name: str, account_type: AccountType) -> User: ...

    @abstractmethod
    async def find_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None: ...

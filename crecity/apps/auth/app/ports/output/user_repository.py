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

    @abstractmethod
    async def soft_delete(self, user_id: int, anonymized_email: str) -> None:
        """탈퇴 처리(§3.8, 갭 #33) — 거래 기록 보존을 위해 행은 남기고 식별정보만 지운다.

        이메일은 unique 제약이 있어 재가입을 막지 않도록 익명값으로 치환한다.
        """
        ...

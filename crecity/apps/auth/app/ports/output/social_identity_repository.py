from __future__ import annotations

from abc import ABC, abstractmethod

from auth.domain.entities.social_identity_entity import SocialIdentity, SocialProvider


class SocialIdentityRepository(ABC):
    """소셜 계정 연결 영속성 포트."""

    @abstractmethod
    async def create(
        self, user_id: int, provider: SocialProvider, provider_user_id: str
    ) -> SocialIdentity: ...

    @abstractmethod
    async def find_by_provider_uid(
        self, provider: SocialProvider, provider_user_id: str
    ) -> SocialIdentity | None: ...

    @abstractmethod
    async def delete_by_user_id(self, user_id: int) -> None:
        """탈퇴 시 소셜 연결 제거 — 같은 소셜 계정으로 재가입할 수 있어야 한다."""
        ...

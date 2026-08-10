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

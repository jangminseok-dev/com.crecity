from __future__ import annotations

from abc import ABC, abstractmethod

from creator.domain.entities.creator_profile_entity import CreatorProfile, ProfileStatus


class CreatorProfileRepository(ABC):
    """프로필 영속성 포트 — 등록·조회 슬라이스가 공유한다(도메인어 명명 예외)."""

    @abstractmethod
    async def create(
        self,
        slug: str,
        name: str,
        tagline: str,
        bio: str,
        location: str | None,
        primary_category: str,
        status: ProfileStatus,
        user_id: int,
    ) -> CreatorProfile: ...

    @abstractmethod
    async def find_by_id(self, profile_id: int) -> CreatorProfile | None: ...

    @abstractmethod
    async def find_by_slug(self, slug: str) -> CreatorProfile | None: ...

    @abstractmethod
    async def find_by_user_id(self, user_id: int) -> CreatorProfile | None:
        """소유 계정으로 조회 — 1인 1프로필 검증에 쓴다."""
        ...

    @abstractmethod
    async def exists_by_slug(self, slug: str) -> bool: ...

    @abstractmethod
    async def list_by_status(
        self,
        status: ProfileStatus,
        category: str | None,
        limit: int,
        offset: int,
    ) -> list[CreatorProfile]:
        """상태로 필터한 프로필을 최신 등록순으로 조회한다."""
        ...

    @abstractmethod
    async def count_by_status(self, status: ProfileStatus, category: str | None) -> int: ...

    @abstractmethod
    async def update_status(
        self, profile_id: int, status: ProfileStatus
    ) -> CreatorProfile | None:
        """심사 상태 전이(허브 심사 계약용) — 대상 없으면 None."""
        ...

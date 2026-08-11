from __future__ import annotations

from abc import ABC, abstractmethod

from creator.domain.entities.profile_analytics_entity import ProfileAnalytics


class AnalyticsRepository(ABC):
    """채널 분석 지표 영속성 포트 — 프로필당 플랫폼 1행(재제출 시 갱신)."""

    @abstractmethod
    async def upsert(
        self,
        profile_id: int,
        platform: str,
        followers_count: int,
        engagement_permille: int | None,
        screenshot_file_name: str,
    ) -> ProfileAnalytics: ...

    @abstractmethod
    async def list_by_profile_id(self, profile_id: int) -> list[ProfileAnalytics]:
        """팔로워 수 내림차순."""
        ...

    @abstractmethod
    async def delete(self, profile_id: int, platform: str) -> bool:
        """삭제 성공 여부 — 없으면 False."""
        ...

    @abstractmethod
    async def followers_total(self, profile_id: int) -> int:
        """전 채널 팔로워 합 — 프로필 헤더 배지(§2.1-2)용."""
        ...

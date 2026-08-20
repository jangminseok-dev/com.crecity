from __future__ import annotations

from abc import ABC, abstractmethod

from creator.domain.entities.profile_analytics_entity import ProfileAnalytics
from creator.domain.value_objects.audience_breakdown import AudienceShare


class AnalyticsRepository(ABC):
    """채널 분석 지표 영속성 포트 — 프로필당 플랫폼 1행(재제출 시 갱신)."""

    @abstractmethod
    # flag_reason(갭 #82): 이상치 사유 — None이면 정상(재제출로 정상값이 오면 자동 해제)
    async def upsert(
        self,
        profile_id: int,
        platform: str,
        followers_count: int,
        engagement_permille: int | None,
        avg_views: int | None,
        screenshot_file_name: str,
        top_audience_region: str | None = None,
        audience: list[AudienceShare] | None = None,
        flag_reason: str | None = None,
    ) -> ProfileAnalytics:
        """채널 지표 저장 — 오디언스 비율(갭 #67)은 **매번 통째로 교체**한다
        (부분 갱신은 합계 검증을 무력화한다)."""
        ...

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

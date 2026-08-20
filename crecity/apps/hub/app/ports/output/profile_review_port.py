from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.profile_review_dto import FlaggedAnalyticsSummary, ProfileReviewSummary


class ProfileReviewPort(ABC):
    """프로필 심사 포트 — 구현은 creator가 제공하고 main.py가 조립한다.

    심사 상태의 소유자는 creator(ProfileStatus) — admin은 이 계약으로만 전이시킨다.
    """

    @abstractmethod
    async def list_pending_profiles(self) -> list[ProfileReviewSummary]:
        """심사 대기(PENDING) 프로필 — 등록 오래된 순."""
        ...

    @abstractmethod
    async def review_profile(
        self, profile_id: int, approved: bool, reason: str | None = None
    ) -> ProfileReviewSummary | None:
        """승인(APPROVED)/반려(REJECTED) 전이 — 대상 없으면 None.

        반려는 사유(reason)를 함께 저장·알림한다(갭 #101) — 사유 없는 반려는
        크리에이터가 보완할 수 없다. 승인 시 reason은 무시된다.
        """
        ...

    @abstractmethod
    async def list_flagged_analytics(self) -> list[FlaggedAnalyticsSummary]:
        """이상치 플래그된 채널 지표(갭 #82) — 오래된 순."""
        ...

    @abstractmethod
    async def clear_analytics_flag(self, analytics_id: int) -> bool:
        """운영자 확인 처리 — 플래그 해제. 대상 없으면 False."""
        ...

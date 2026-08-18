from __future__ import annotations

from abc import ABC, abstractmethod

from admin.app.dtos.analytics_review_dto import ClearFlagCommand
from hub.app.dtos.profile_review_dto import FlaggedAnalyticsSummary


class AnalyticsReviewUseCase(ABC):
    """이상치 지표 재검토(갭 #82).

    Raises:
        ReviewTargetNotFoundError: 플래그 대상 없음.
    """

    @abstractmethod
    async def list_flagged(self) -> list[FlaggedAnalyticsSummary]: ...

    @abstractmethod
    async def clear_flag(self, command: ClearFlagCommand) -> None: ...

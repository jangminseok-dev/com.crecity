from __future__ import annotations

from abc import ABC, abstractmethod

from admin.app.dtos.profile_review_dto import ReviewDecisionCommand
from hub.app.dtos.profile_review_dto import ProfileReviewSummary


class ProfileReviewUseCase(ABC):
    """프로필 심사 유스케이스 — `profile.review` 권한 보유자(운영자) 전용.

    심사 상태의 소유자는 creator — 전이는 허브 ProfileReviewPort 계약을 경유한다.
    """

    @abstractmethod
    async def list_pending(self) -> list[ProfileReviewSummary]:
        """심사 대기 프로필 — 오래 기다린 순."""
        ...

    @abstractmethod
    async def review(self, command: ReviewDecisionCommand) -> ProfileReviewSummary:
        """승인/반려 결정을 반영하고 감사 기록을 남긴다.

        Raises:
            ReviewTargetNotFoundError: 대상 프로필 없음.
        """
        ...

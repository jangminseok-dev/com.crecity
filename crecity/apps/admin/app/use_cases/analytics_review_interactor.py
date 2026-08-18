from __future__ import annotations

from admin.app.dtos.analytics_review_dto import ClearFlagCommand
from admin.app.exceptions import ReviewTargetNotFoundError
from admin.app.ports.input.analytics_review_use_case import AnalyticsReviewUseCase
from admin.app.ports.output.review_record_port import ReviewRecordPort
from hub.app.dtos.profile_review_dto import FlaggedAnalyticsSummary
from hub.app.ports.output.profile_review_port import ProfileReviewPort


class AnalyticsReviewInteractor(AnalyticsReviewUseCase):
    """이상치 플래그 재검토(갭 #82) — 지표 소유자는 creator라 허브 계약으로만 만진다."""

    def __init__(self, profiles: ProfileReviewPort, record: ReviewRecordPort) -> None:
        self._profiles = profiles
        self._record = record

    async def list_flagged(self) -> list[FlaggedAnalyticsSummary]:
        return await self._profiles.list_flagged_analytics()

    async def clear_flag(self, command: ClearFlagCommand) -> None:
        if not await self._profiles.clear_analytics_flag(command.analytics_id):
            raise ReviewTargetNotFoundError(
                f"플래그된 지표를 찾을 수 없습니다: {command.analytics_id}"
            )
        await self._record.record(
            subject="analytics_review",
            note=(
                f"이상치 지표 {command.analytics_id} 확인 처리 — "
                f"처리자 {command.reviewer_email}(user_id={command.reviewer_id})"
            ),
        )

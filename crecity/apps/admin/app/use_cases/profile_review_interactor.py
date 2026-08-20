from __future__ import annotations

from admin.app.dtos.profile_review_dto import ReviewDecisionCommand
from admin.app.exceptions import ReviewTargetNotFoundError
from admin.app.ports.input.profile_review_use_case import ProfileReviewUseCase
from admin.app.ports.output.review_record_port import ReviewRecordPort
from hub.app.dtos.profile_review_dto import ProfileReviewSummary
from hub.app.ports.output.profile_review_port import ProfileReviewPort


class ProfileReviewInteractor(ProfileReviewUseCase):

    def __init__(self, profiles: ProfileReviewPort, record: ReviewRecordPort) -> None:
        self._profiles = profiles
        self._record = record

    async def list_pending(self) -> list[ProfileReviewSummary]:
        return await self._profiles.list_pending_profiles()

    async def review(self, command: ReviewDecisionCommand) -> ProfileReviewSummary:
        result = await self._profiles.review_profile(
            command.profile_id, command.approved, reason=command.reason
        )
        if result is None:
            raise ReviewTargetNotFoundError(f"심사 대상을 찾을 수 없습니다: {command.profile_id}")
        decision = "승인" if command.approved else f"반려(사유: {command.reason})"
        await self._record.record(
            subject="profile_review",
            note=(
                f"프로필 {result.id}({result.slug}) {decision} — "
                f"심사자 {command.reviewer_email}(user_id={command.reviewer_id})"
            ),
        )
        return result

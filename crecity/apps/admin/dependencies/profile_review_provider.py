from __future__ import annotations

from admin.adapter.outbound.log_review_record_adapter import LogReviewRecordAdapter
from admin.app.ports.input.profile_review_use_case import ProfileReviewUseCase
from admin.app.use_cases.profile_review_interactor import ProfileReviewInteractor
from hub.dependencies.profile_review_provider import get_profile_review_port


def get_profile_review_use_case() -> ProfileReviewUseCase:
    return ProfileReviewInteractor(
        profiles=get_profile_review_port(),
        record=LogReviewRecordAdapter(),
    )

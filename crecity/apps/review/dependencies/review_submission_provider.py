from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from hub.dependencies.order_participants_provider import get_order_participants_port
from review.adapter.outbound.pg.review_pg_repository import ReviewPgRepository
from review.app.ports.input.review_submission_use_case import ReviewSubmissionUseCase
from review.app.use_cases.review_submission_interactor import ReviewSubmissionInteractor


def get_review_submission_use_case(
    db: AsyncSession = Depends(get_db),
) -> ReviewSubmissionUseCase:
    return ReviewSubmissionInteractor(
        reviews=ReviewPgRepository(session=db),
        orders=get_order_participants_port(),
    )

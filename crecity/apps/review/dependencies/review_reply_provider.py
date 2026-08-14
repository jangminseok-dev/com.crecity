from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from review.adapter.outbound.pg.review_pg_repository import ReviewPgRepository
from review.app.ports.input.review_reply_use_case import ReviewReplyUseCase
from review.app.use_cases.review_reply_interactor import ReviewReplyInteractor


def get_review_reply_use_case(db: AsyncSession = Depends(get_db)) -> ReviewReplyUseCase:
    return ReviewReplyInteractor(reviews=ReviewPgRepository(session=db))

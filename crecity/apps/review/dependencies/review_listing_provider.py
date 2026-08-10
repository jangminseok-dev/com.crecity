from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from hub.dependencies.creator_ref_provider import get_creator_ref_port
from review.adapter.outbound.pg.review_pg_repository import ReviewPgRepository
from review.app.ports.input.review_listing_use_case import ReviewListingUseCase
from review.app.use_cases.review_listing_interactor import ReviewListingInteractor


def get_review_listing_use_case(
    db: AsyncSession = Depends(get_db),
) -> ReviewListingUseCase:
    return ReviewListingInteractor(
        reviews=ReviewPgRepository(session=db),
        creators=get_creator_ref_port(),
    )

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from hub.dependencies.order_participants_provider import get_order_participants_port
from review.adapter.outbound.pg.brand_review_pg_repository import BrandReviewPgRepository
from review.app.ports.input.brand_review_use_case import BrandReviewUseCase
from review.app.use_cases.brand_review_interactor import BrandReviewInteractor


def get_brand_review_use_case(
    db: AsyncSession = Depends(get_db),
) -> BrandReviewUseCase:
    return BrandReviewInteractor(
        reviews=BrandReviewPgRepository(session=db),
        orders=get_order_participants_port(),
    )

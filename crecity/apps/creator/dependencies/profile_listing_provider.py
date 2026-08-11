from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from creator.adapter.outbound.pg.creator_package_pg_repository import CreatorPackagePgRepository
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.adapter.outbound.pg.portfolio_item_pg_repository import PortfolioItemPgRepository
from creator.app.ports.input.profile_listing_use_case import ProfileListingUseCase
from creator.app.use_cases.profile_listing_interactor import ProfileListingInteractor
from hub.dependencies.creator_rating_provider import get_creator_rating_port


def get_profile_listing_use_case(
    db: AsyncSession = Depends(get_db),
) -> ProfileListingUseCase:
    return ProfileListingInteractor(
        repository=CreatorProfilePgRepository(session=db),
        packages=CreatorPackagePgRepository(session=db),
        portfolio=PortfolioItemPgRepository(session=db),
        ratings=get_creator_rating_port(),
    )

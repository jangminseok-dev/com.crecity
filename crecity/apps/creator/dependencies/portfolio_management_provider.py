from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from creator.adapter.outbound.local_portfolio_file_storage import LocalPortfolioFileStorage
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.adapter.outbound.pg.portfolio_item_pg_repository import PortfolioItemPgRepository
from creator.app.ports.input.portfolio_management_use_case import PortfolioManagementUseCase
from creator.app.use_cases.portfolio_management_interactor import PortfolioManagementInteractor


def get_portfolio_management_use_case(
    db: AsyncSession = Depends(get_db),
) -> PortfolioManagementUseCase:
    return PortfolioManagementInteractor(
        profiles=CreatorProfilePgRepository(session=db),
        items=PortfolioItemPgRepository(session=db),
        storage=LocalPortfolioFileStorage(),
    )

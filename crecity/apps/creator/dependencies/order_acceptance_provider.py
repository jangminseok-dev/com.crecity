from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.app.ports.input.order_acceptance_use_case import OrderAcceptanceUseCase
from creator.app.use_cases.order_acceptance_interactor import OrderAcceptanceInteractor


def get_order_acceptance_use_case(
    db: AsyncSession = Depends(get_db),
) -> OrderAcceptanceUseCase:
    return OrderAcceptanceInteractor(repository=CreatorProfilePgRepository(session=db))

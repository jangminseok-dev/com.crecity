from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.app.ports.input.profile_update_use_case import ProfileUpdateUseCase
from creator.app.use_cases.profile_update_interactor import ProfileUpdateInteractor


def get_profile_update_use_case(
    db: AsyncSession = Depends(get_db),
) -> ProfileUpdateUseCase:
    return ProfileUpdateInteractor(repository=CreatorProfilePgRepository(session=db))

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.app.ports.input.profile_lookup_use_case import ProfileLookupUseCase
from creator.app.use_cases.profile_lookup_interactor import ProfileLookupInteractor


def get_profile_lookup_use_case(
    db: AsyncSession = Depends(get_db),
) -> ProfileLookupUseCase:
    return ProfileLookupInteractor(repository=CreatorProfilePgRepository(session=db))

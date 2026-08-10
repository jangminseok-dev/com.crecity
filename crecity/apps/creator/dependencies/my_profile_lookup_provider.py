from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.app.ports.input.my_profile_lookup_use_case import MyProfileLookupUseCase
from creator.app.use_cases.my_profile_lookup_interactor import MyProfileLookupInteractor


def get_my_profile_lookup_use_case(
    db: AsyncSession = Depends(get_db),
) -> MyProfileLookupUseCase:
    return MyProfileLookupInteractor(repository=CreatorProfilePgRepository(session=db))

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.app.ports.input.profile_registration_use_case import ProfileRegistrationUseCase
from creator.app.use_cases.profile_registration_interactor import ProfileRegistrationInteractor


def get_profile_registration_use_case(
    db: AsyncSession = Depends(get_db),
) -> ProfileRegistrationUseCase:
    return ProfileRegistrationInteractor(repository=CreatorProfilePgRepository(session=db))

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.app.ports.input.profile_resubmission_use_case import ProfileResubmissionUseCase
from creator.app.use_cases.profile_resubmission_interactor import ProfileResubmissionInteractor


def get_profile_resubmission_use_case(
    db: AsyncSession = Depends(get_db),
) -> ProfileResubmissionUseCase:
    return ProfileResubmissionInteractor(repository=CreatorProfilePgRepository(session=db))

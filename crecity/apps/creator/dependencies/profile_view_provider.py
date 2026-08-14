from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.adapter.outbound.pg.profile_view_pg_repository import ProfileViewPgRepository
from creator.app.ports.input.profile_view_use_case import ProfileViewUseCase
from creator.app.use_cases.profile_view_interactor import ProfileViewInteractor


def get_profile_view_use_case(db: AsyncSession = Depends(get_db)) -> ProfileViewUseCase:
    return ProfileViewInteractor(
        profiles=CreatorProfilePgRepository(session=db),
        views=ProfileViewPgRepository(session=db),
    )

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from creator.adapter.outbound.pg.creator_package_pg_repository import CreatorPackagePgRepository
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.app.ports.input.package_management_use_case import PackageManagementUseCase
from creator.app.use_cases.package_management_interactor import PackageManagementInteractor


def get_package_management_use_case(
    db: AsyncSession = Depends(get_db),
) -> PackageManagementUseCase:
    return PackageManagementInteractor(
        profiles=CreatorProfilePgRepository(session=db),
        packages=CreatorPackagePgRepository(session=db),
    )

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from creator.adapter.outbound.pg.creator_profile_pg_repository import CreatorProfilePgRepository
from creator.adapter.outbound.pg.faq_pg_repository import FaqPgRepository
from creator.app.ports.input.faq_management_use_case import FaqManagementUseCase
from creator.app.use_cases.faq_management_interactor import FaqManagementInteractor


def get_faq_management_use_case(
    db: AsyncSession = Depends(get_db),
) -> FaqManagementUseCase:
    return FaqManagementInteractor(
        profiles=CreatorProfilePgRepository(session=db),
        faqs=FaqPgRepository(session=db),
    )

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from campaign.adapter.outbound.pg.application_pg_repository import ApplicationPgRepository
from campaign.adapter.outbound.pg.campaign_pg_repository import CampaignPgRepository
from campaign.app.ports.input.campaign_application_use_case import CampaignApplicationUseCase
from campaign.app.use_cases.campaign_application_interactor import (
    CampaignApplicationInteractor,
)
from core.database import get_db
from hub.dependencies.creator_ref_provider import get_creator_ref_port


def get_campaign_application_use_case(
    db: AsyncSession = Depends(get_db),
) -> CampaignApplicationUseCase:
    return CampaignApplicationInteractor(
        campaigns=CampaignPgRepository(session=db),
        applications=ApplicationPgRepository(session=db),
        creators=get_creator_ref_port(),
    )

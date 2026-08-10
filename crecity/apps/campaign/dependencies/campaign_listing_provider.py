from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from campaign.adapter.outbound.pg.campaign_pg_repository import CampaignPgRepository
from campaign.app.ports.input.campaign_listing_use_case import CampaignListingUseCase
from campaign.app.use_cases.campaign_listing_interactor import CampaignListingInteractor
from core.database import get_db


def get_campaign_listing_use_case(
    db: AsyncSession = Depends(get_db),
) -> CampaignListingUseCase:
    return CampaignListingInteractor(campaigns=CampaignPgRepository(session=db))

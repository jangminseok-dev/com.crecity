from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from campaign.adapter.outbound.pg.campaign_pg_repository import CampaignPgRepository
from campaign.app.ports.input.campaign_posting_use_case import CampaignPostingUseCase
from campaign.app.use_cases.campaign_posting_interactor import CampaignPostingInteractor
from core.database import get_db


def get_campaign_posting_use_case(
    db: AsyncSession = Depends(get_db),
) -> CampaignPostingUseCase:
    return CampaignPostingInteractor(campaigns=CampaignPgRepository(session=db))

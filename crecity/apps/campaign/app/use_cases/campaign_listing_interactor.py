from __future__ import annotations

from campaign.app.dtos.campaign_listing_dto import CampaignDetailQuery, OpenCampaignsQuery
from campaign.app.dtos.campaign_posting_dto import CampaignResult
from campaign.app.exceptions import CampaignNotFoundError
from campaign.app.ports.input.campaign_listing_use_case import CampaignListingUseCase
from campaign.app.ports.output.campaign_repository import CampaignRepository
from campaign.app.use_cases.campaign_posting_interactor import to_result
from campaign.domain.entities.campaign_entity import CampaignStatus


class CampaignListingInteractor(CampaignListingUseCase):

    def __init__(self, campaigns: CampaignRepository) -> None:
        self._campaigns = campaigns

    async def list_open(self, query: OpenCampaignsQuery) -> list[CampaignResult]:
        campaigns = await self._campaigns.list_by_status(
            CampaignStatus.OPEN, limit=query.limit, offset=query.offset
        )
        return [to_result(campaign) for campaign in campaigns]

    async def get_campaign(self, query: CampaignDetailQuery) -> CampaignResult:
        campaign = await self._campaigns.find_by_id(query.campaign_id)
        if campaign is None:
            raise CampaignNotFoundError(f"공고를 찾을 수 없습니다: {query.campaign_id}")
        return to_result(campaign)

    async def list_my_campaigns(self, brand_user_id: int) -> list[CampaignResult]:
        campaigns = await self._campaigns.list_by_brand(brand_user_id)
        return [to_result(campaign) for campaign in campaigns]

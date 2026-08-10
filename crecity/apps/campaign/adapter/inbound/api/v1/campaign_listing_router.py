from fastapi import APIRouter, Depends, HTTPException, Query

from campaign.adapter.inbound.api.schemas.campaign_posting_schema import CampaignResponseSchema
from campaign.adapter.inbound.api.v1.campaign_posting_router import _to_schema
from campaign.app.dtos.campaign_listing_dto import CampaignDetailQuery, OpenCampaignsQuery
from campaign.app.exceptions import CampaignNotFoundError
from campaign.app.ports.input.campaign_listing_use_case import CampaignListingUseCase
from campaign.dependencies.campaign_listing_provider import get_campaign_listing_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

campaign_listing_router = APIRouter(prefix="/campaign", tags=["campaign"])


@campaign_listing_router.get("/campaigns", response_model=list[CampaignResponseSchema])
async def list_open_campaigns(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    user: VerifiedUser = Depends(get_current_user),
    use_case: CampaignListingUseCase = Depends(get_campaign_listing_use_case),
) -> list[CampaignResponseSchema]:
    results = await use_case.list_open(OpenCampaignsQuery(limit=limit, offset=offset))
    return [_to_schema(result) for result in results]


@campaign_listing_router.get("/my/campaigns", response_model=list[CampaignResponseSchema])
async def list_my_campaigns(
    user: VerifiedUser = Depends(get_current_user),
    use_case: CampaignListingUseCase = Depends(get_campaign_listing_use_case),
) -> list[CampaignResponseSchema]:
    results = await use_case.list_my_campaigns(user.id)
    return [_to_schema(result) for result in results]


@campaign_listing_router.get("/campaigns/{campaign_id}", response_model=CampaignResponseSchema)
async def get_campaign(
    campaign_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: CampaignListingUseCase = Depends(get_campaign_listing_use_case),
) -> CampaignResponseSchema:
    try:
        result = await use_case.get_campaign(CampaignDetailQuery(campaign_id=campaign_id))
    except CampaignNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return _to_schema(result)

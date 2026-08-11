from fastapi import APIRouter, Depends, HTTPException

from campaign.adapter.inbound.api.schemas.campaign_posting_schema import (
    CampaignResponseSchema,
    PostCampaignRequestSchema,
)
from campaign.app.dtos.campaign_posting_dto import CloseCampaignCommand, PostCampaignCommand
from campaign.app.exceptions import CampaignNotFoundError, NotBrandAccountError
from campaign.app.ports.input.campaign_posting_use_case import CampaignPostingUseCase
from campaign.dependencies.campaign_posting_provider import get_campaign_posting_use_case
from campaign.domain.entities.campaign_entity import (
    InvalidCampaignStateError,
    NotCampaignOwnerError,
)
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

campaign_posting_router = APIRouter(prefix="/campaign", tags=["campaign"])


def _to_schema(result) -> CampaignResponseSchema:
    return CampaignResponseSchema(
        id=result.id,
        brand_user_id=result.brand_user_id,
        title=result.title,
        description=result.description,
        platform=result.platform,
        budget_krw=result.budget_krw,
        status=result.status,
        deadline_at=result.deadline_at,
        target_category=result.target_category,
        target_location=result.target_location,
        created_at=result.created_at,
    )


@campaign_posting_router.post("/campaigns", response_model=CampaignResponseSchema, status_code=201)
async def post_campaign(
    body: PostCampaignRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: CampaignPostingUseCase = Depends(get_campaign_posting_use_case),
) -> CampaignResponseSchema:
    try:
        result = await use_case.post(
            PostCampaignCommand(
                title=body.title,
                description=body.description,
                platform=body.platform,
                budget_krw=body.budget_krw,
                brand_user_id=user.id,
                account_type=user.account_type,
                deadline_at=body.deadline_at,
                target_category=body.target_category,
                target_location=body.target_location,
            )
        )
    except NotBrandAccountError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return _to_schema(result)


@campaign_posting_router.post(
    "/campaigns/{campaign_id}/close", response_model=CampaignResponseSchema
)
async def close_campaign(
    campaign_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: CampaignPostingUseCase = Depends(get_campaign_posting_use_case),
) -> CampaignResponseSchema:
    try:
        result = await use_case.close(
            CloseCampaignCommand(campaign_id=campaign_id, actor_user_id=user.id)
        )
    except CampaignNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotCampaignOwnerError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except InvalidCampaignStateError as error:
        raise HTTPException(status_code=409, detail=str(error))
    return _to_schema(result)

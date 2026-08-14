from fastapi import APIRouter, Depends, HTTPException, Query

from campaign.adapter.inbound.api.schemas.campaign_application_schema import (
    ApplicationResponseSchema,
    ApplyRequestSchema,
)
from campaign.app.dtos.campaign_application_dto import ApplicationsQuery, ApplyCommand
from campaign.app.exceptions import (
    AlreadyAppliedError,
    CampaignNotFoundError,
    CreatorProfileRequiredError,
    NotCreatorAccountError,
)
from campaign.app.ports.input.campaign_application_use_case import CampaignApplicationUseCase
from campaign.dependencies.campaign_application_provider import (
    get_campaign_application_use_case,
)
from campaign.domain.entities.campaign_entity import (
    InvalidCampaignStateError,
    NotCampaignOwnerError,
)
from campaign.domain.value_objects.application_sort import ApplicationSort
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

campaign_application_router = APIRouter(prefix="/campaign", tags=["campaign"])


def _to_schema(result) -> ApplicationResponseSchema:
    return ApplicationResponseSchema(
        id=result.id,
        campaign_id=result.campaign_id,
        creator_user_id=result.creator_user_id,
        creator_name=result.creator_name,
        creator_slug=result.creator_slug,
        message=result.message,
        proposed_price_krw=result.proposed_price_krw,
        order_id=result.order_id,
        created_at=result.created_at,
    )


@campaign_application_router.post(
    "/campaigns/{campaign_id}/applications",
    response_model=ApplicationResponseSchema,
    status_code=201,
)
async def apply_to_campaign(
    campaign_id: int,
    body: ApplyRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: CampaignApplicationUseCase = Depends(get_campaign_application_use_case),
) -> ApplicationResponseSchema:
    try:
        result = await use_case.apply(
            ApplyCommand(
                campaign_id=campaign_id,
                creator_user_id=user.id,
                account_type=user.account_type,
                message=body.message,
                proposed_price_krw=body.proposed_price_krw,
            )
        )
    except CampaignNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except (NotCreatorAccountError, CreatorProfileRequiredError) as error:
        raise HTTPException(status_code=403, detail=str(error))
    except (AlreadyAppliedError, InvalidCampaignStateError) as error:
        raise HTTPException(status_code=409, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return _to_schema(result)


@campaign_application_router.get(
    "/campaigns/{campaign_id}/applications", response_model=list[ApplicationResponseSchema]
)
async def list_applications(
    campaign_id: int,
    sort: ApplicationSort = Query(ApplicationSort.OLDEST, description="지원자 정렬(갭 #70)"),
    only_open: bool = Query(False, description="아직 수락하지 않은 지원만"),
    user: VerifiedUser = Depends(get_current_user),
    use_case: CampaignApplicationUseCase = Depends(get_campaign_application_use_case),
) -> list[ApplicationResponseSchema]:
    try:
        results = await use_case.list_applications(
            ApplicationsQuery(
                campaign_id=campaign_id,
                requester_user_id=user.id,
                sort=sort,
                only_open=only_open,
            )
        )
    except CampaignNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotCampaignOwnerError as error:
        raise HTTPException(status_code=403, detail=str(error))
    return [_to_schema(result) for result in results]

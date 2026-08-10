from fastapi import APIRouter, Depends

from review.adapter.inbound.api.schemas.appraiser_schema import AppraiserResponseSchema
from review.app.dtos.appraiser_dto import AppraiserQuery
from review.app.ports.input.appraiser_use_case import AppraiserUseCase
from review.dependencies.appraiser_provider import get_appraiser_use_case

appraiser_router = APIRouter(prefix="/review", tags=["review"])


@appraiser_router.get("/myself", response_model=AppraiserResponseSchema)
async def introduce_myself(
    appraiser: AppraiserUseCase = Depends(get_appraiser_use_case),
) -> AppraiserResponseSchema:
    result = await appraiser.introduce_myself(AppraiserQuery(id=7, name="리뷰 (review)"))
    return AppraiserResponseSchema(
        id=result.id, name=result.name, introduction=result.introduction
    )

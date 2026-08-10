from fastapi import APIRouter, Depends

from campaign.adapter.inbound.api.schemas.herald_schema import HeraldResponseSchema
from campaign.app.dtos.herald_dto import HeraldQuery
from campaign.app.ports.input.herald_use_case import HeraldUseCase
from campaign.dependencies.herald_provider import get_herald_use_case

herald_router = APIRouter(prefix="/campaign", tags=["campaign"])


@herald_router.get("/myself", response_model=HeraldResponseSchema)
async def introduce_myself(
    herald: HeraldUseCase = Depends(get_herald_use_case),
) -> HeraldResponseSchema:
    result = await herald.introduce_myself(HeraldQuery(id=8, name="캠페인 (campaign)"))
    return HeraldResponseSchema(id=result.id, name=result.name, introduction=result.introduction)

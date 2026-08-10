from fastapi import APIRouter, Depends

from admin.adapter.inbound.api.schemas.steward_schema import StewardResponseSchema
from admin.app.dtos.steward_dto import StewardQuery
from admin.app.ports.input.steward_use_case import StewardUseCase
from admin.dependencies.steward_provider import get_steward_use_case

steward_router = APIRouter(prefix="/admin", tags=["admin"])


@steward_router.get("/myself", response_model=StewardResponseSchema)
async def introduce_myself(
    steward: StewardUseCase = Depends(get_steward_use_case),
) -> StewardResponseSchema:
    result = await steward.introduce_myself(StewardQuery(id=5, name="운영 (admin)"))
    return StewardResponseSchema(id=result.id, name=result.name, introduction=result.introduction)

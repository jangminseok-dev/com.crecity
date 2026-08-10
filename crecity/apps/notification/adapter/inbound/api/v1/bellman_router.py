from fastapi import APIRouter, Depends

from notification.adapter.inbound.api.schemas.bellman_schema import BellmanResponseSchema
from notification.app.dtos.bellman_dto import BellmanQuery
from notification.app.ports.input.bellman_use_case import BellmanUseCase
from notification.dependencies.bellman_provider import get_bellman_use_case

bellman_router = APIRouter(prefix="/notification", tags=["notification"])


@bellman_router.get("/myself", response_model=BellmanResponseSchema)
async def introduce_myself(
    bellman: BellmanUseCase = Depends(get_bellman_use_case),
) -> BellmanResponseSchema:
    result = await bellman.introduce_myself(BellmanQuery(id=10, name="알림 (notification)"))
    return BellmanResponseSchema(id=result.id, name=result.name, introduction=result.introduction)

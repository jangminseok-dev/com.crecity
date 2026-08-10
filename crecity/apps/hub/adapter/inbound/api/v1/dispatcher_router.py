from fastapi import APIRouter, Depends

from hub.adapter.inbound.api.schemas.dispatcher_schema import DispatcherResponseSchema
from hub.app.dtos.dispatcher_dto import DispatcherQuery
from hub.app.ports.input.dispatcher_use_case import DispatcherUseCase
from hub.dependencies.dispatcher_provider import get_dispatcher_use_case

dispatcher_router = APIRouter(prefix="/hub", tags=["hub"])


@dispatcher_router.get("/myself", response_model=DispatcherResponseSchema)
async def introduce_myself(
    dispatcher: DispatcherUseCase = Depends(get_dispatcher_use_case),
) -> DispatcherResponseSchema:
    result = await dispatcher.introduce_myself(
        DispatcherQuery(
            id=1,
            name="허브 (hub)",
        )
    )
    return DispatcherResponseSchema(
        id=result.id, name=result.name, introduction=result.introduction
    )

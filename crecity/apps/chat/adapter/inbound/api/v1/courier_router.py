from fastapi import APIRouter, Depends

from chat.adapter.inbound.api.schemas.courier_schema import CourierResponseSchema
from chat.app.dtos.courier_dto import CourierQuery
from chat.app.ports.input.courier_use_case import CourierUseCase
from chat.dependencies.courier_provider import get_courier_use_case

courier_router = APIRouter(prefix="/chat", tags=["chat"])


@courier_router.get("/myself", response_model=CourierResponseSchema)
async def introduce_myself(
    courier: CourierUseCase = Depends(get_courier_use_case),
) -> CourierResponseSchema:
    result = await courier.introduce_myself(CourierQuery(id=9, name="채팅 (chat)"))
    return CourierResponseSchema(id=result.id, name=result.name, introduction=result.introduction)

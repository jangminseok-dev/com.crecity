from fastapi import APIRouter, Depends

from order.adapter.inbound.api.schemas.bookkeeper_schema import BookkeeperResponseSchema
from order.app.dtos.bookkeeper_dto import BookkeeperQuery
from order.app.ports.input.bookkeeper_use_case import BookkeeperUseCase
from order.dependencies.bookkeeper_provider import get_bookkeeper_use_case

bookkeeper_router = APIRouter(prefix="/order", tags=["order"])


@bookkeeper_router.get("/myself", response_model=BookkeeperResponseSchema)
async def introduce_myself(
    bookkeeper: BookkeeperUseCase = Depends(get_bookkeeper_use_case),
) -> BookkeeperResponseSchema:
    result = await bookkeeper.introduce_myself(BookkeeperQuery(id=4, name="주문 (order)"))
    return BookkeeperResponseSchema(
        id=result.id, name=result.name, introduction=result.introduction
    )

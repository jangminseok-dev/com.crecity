from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from order.adapter.inbound.api.schemas.order_result_schema import OrderResponseSchema
from order.app.dtos.order_lookup_dto import MyOrdersQuery, OrderDetailQuery
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.ports.input.order_lookup_use_case import OrderLookupUseCase
from order.dependencies.order_lookup_provider import get_order_lookup_use_case

order_lookup_router = APIRouter(prefix="/order", tags=["order"])


@order_lookup_router.get("/orders", response_model=list[OrderResponseSchema])
async def list_my_orders(
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderLookupUseCase = Depends(get_order_lookup_use_case),
) -> list[OrderResponseSchema]:
    results = await use_case.list_my_orders(MyOrdersQuery(user_id=user.id))
    return [OrderResponseSchema.from_result(result) for result in results]


@order_lookup_router.get("/orders/{order_id}", response_model=OrderResponseSchema)
async def get_order(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderLookupUseCase = Depends(get_order_lookup_use_case),
) -> OrderResponseSchema:
    try:
        result = await use_case.get_order(
            OrderDetailQuery(order_id=order_id, requester_user_id=user.id)
        )
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderParticipantError as error:
        raise HTTPException(status_code=403, detail=str(error))
    return OrderResponseSchema.from_result(result)

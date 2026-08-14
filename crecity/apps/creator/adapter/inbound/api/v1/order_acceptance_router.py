from fastapi import APIRouter, Depends, HTTPException

from creator.adapter.inbound.api.schemas.order_acceptance_schema import (
    OrderAcceptanceRequestSchema,
    OrderAcceptanceResponseSchema,
)
from creator.app.dtos.order_acceptance_dto import OrderAcceptanceCommand
from creator.app.exceptions import ProfileNotFoundError
from creator.app.ports.input.order_acceptance_use_case import OrderAcceptanceUseCase
from creator.dependencies.order_acceptance_provider import get_order_acceptance_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

order_acceptance_router = APIRouter(prefix="/creator", tags=["creator"])


@order_acceptance_router.put(
    "/my/profile/accepting-orders", response_model=OrderAcceptanceResponseSchema
)
async def set_accepting_orders(
    body: OrderAcceptanceRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderAcceptanceUseCase = Depends(get_order_acceptance_use_case),
) -> OrderAcceptanceResponseSchema:
    """주문 수신 켜기·끄기(갭 #64) — 끄면 목록에서 빠지고 새 주문을 받지 않는다."""
    try:
        result = await use_case.set_accepting(
            OrderAcceptanceCommand(user_id=user.id, accepting=body.accepting)
        )
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return OrderAcceptanceResponseSchema.from_result(result)

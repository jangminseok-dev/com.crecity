from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from order.adapter.inbound.api.schemas.order_placement_schema import OrderPlacementRequestSchema
from order.adapter.inbound.api.schemas.order_result_schema import OrderResponseSchema
from order.app.dtos.order_placement_dto import OrderPlacementCommand
from order.app.exceptions import NotBrandAccountError, PackageNotOrderableError
from order.app.ports.input.order_placement_use_case import OrderPlacementUseCase
from order.dependencies.order_placement_provider import get_order_placement_use_case

order_placement_router = APIRouter(prefix="/order", tags=["order"])


@order_placement_router.post("/orders", response_model=OrderResponseSchema, status_code=201)
async def place_order(
    body: OrderPlacementRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderPlacementUseCase = Depends(get_order_placement_use_case),
) -> OrderResponseSchema:
    try:
        result = await use_case.place(
            OrderPlacementCommand(
                package_id=body.package_id,
                requirements=body.requirements,
                brand_user_id=user.id,
                account_type=user.account_type,
            )
        )
    except NotBrandAccountError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except PackageNotOrderableError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return OrderResponseSchema.from_result(result)

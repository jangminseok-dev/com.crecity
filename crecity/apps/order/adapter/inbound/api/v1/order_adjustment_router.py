from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from order.adapter.inbound.api.schemas.order_adjustment_schema import (
    AdjustmentRequestSchema,
    AdjustmentResponseSchema,
)
from order.app.dtos.order_adjustment_dto import (
    AdjustmentListQuery,
    DeclineAdjustmentCommand,
    RequestAdjustmentCommand,
)
from order.app.exceptions import (
    AdjustmentNotFoundError,
    DuplicateAdjustmentError,
    NotOrderParticipantError,
    OrderNotFoundError,
)
from order.app.ports.input.order_adjustment_use_case import OrderAdjustmentUseCase
from order.dependencies.order_adjustment_provider import get_order_adjustment_use_case
from order.domain.entities.order_adjustment_entity import InvalidAdjustmentError
from order.domain.entities.order_entity import InvalidOrderTransitionError, NotOrderActorError

order_adjustment_router = APIRouter(prefix="/order", tags=["order"])


@order_adjustment_router.post(
    "/orders/{order_id}/adjustments", response_model=AdjustmentResponseSchema, status_code=201
)
async def request_adjustment(
    order_id: int,
    body: AdjustmentRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderAdjustmentUseCase = Depends(get_order_adjustment_use_case),
) -> AdjustmentResponseSchema:
    try:
        result = await use_case.request(
            RequestAdjustmentCommand(
                order_id=order_id,
                actor_user_id=user.id,
                extra_amount_krw=body.extra_amount_krw,
                reason=body.reason,
            )
        )
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderActorError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except (InvalidOrderTransitionError, DuplicateAdjustmentError) as error:
        raise HTTPException(status_code=409, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return AdjustmentResponseSchema.from_result(result)


@order_adjustment_router.get(
    "/orders/{order_id}/adjustments", response_model=list[AdjustmentResponseSchema]
)
async def list_adjustments(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderAdjustmentUseCase = Depends(get_order_adjustment_use_case),
) -> list[AdjustmentResponseSchema]:
    try:
        results = await use_case.list_by_order(
            AdjustmentListQuery(order_id=order_id, requester_user_id=user.id)
        )
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderParticipantError as error:
        raise HTTPException(status_code=403, detail=str(error))
    return [AdjustmentResponseSchema.from_result(result) for result in results]


@order_adjustment_router.post(
    "/adjustments/{adjustment_id}/decline", response_model=AdjustmentResponseSchema
)
async def decline_adjustment(
    adjustment_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderAdjustmentUseCase = Depends(get_order_adjustment_use_case),
) -> AdjustmentResponseSchema:
    try:
        result = await use_case.decline(
            DeclineAdjustmentCommand(adjustment_id=adjustment_id, actor_user_id=user.id)
        )
    except (AdjustmentNotFoundError, OrderNotFoundError) as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderActorError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except InvalidAdjustmentError as error:
        raise HTTPException(status_code=409, detail=str(error))
    return AdjustmentResponseSchema.from_result(result)

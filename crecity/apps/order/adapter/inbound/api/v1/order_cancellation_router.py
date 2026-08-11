from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from order.adapter.inbound.api.schemas.order_result_schema import OrderResponseSchema
from order.app.dtos.order_cancellation_dto import CancellationCommand
from order.app.dtos.order_result_dto import OrderResult
from order.app.exceptions import OrderNotFoundError
from order.app.ports.input.order_cancellation_use_case import OrderCancellationUseCase
from order.dependencies.order_cancellation_provider import get_order_cancellation_use_case
from order.domain.entities.order_entity import InvalidOrderTransitionError, NotOrderActorError

order_cancellation_router = APIRouter(prefix="/order", tags=["order"])


async def _cancellation(
    action: Callable[[CancellationCommand], Awaitable[OrderResult]],
    order_id: int,
    user: VerifiedUser,
) -> OrderResponseSchema:
    try:
        result = await action(CancellationCommand(order_id=order_id, actor_user_id=user.id))
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderActorError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except InvalidOrderTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error))
    return OrderResponseSchema.from_result(result)


@order_cancellation_router.post(
    "/orders/{order_id}/cancel-request", response_model=OrderResponseSchema
)
async def request_cancellation(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderCancellationUseCase = Depends(get_order_cancellation_use_case),
) -> OrderResponseSchema:
    return await _cancellation(use_case.request, order_id, user)


@order_cancellation_router.post(
    "/orders/{order_id}/cancel-consent", response_model=OrderResponseSchema
)
async def consent_cancellation(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderCancellationUseCase = Depends(get_order_cancellation_use_case),
) -> OrderResponseSchema:
    return await _cancellation(use_case.consent, order_id, user)


@order_cancellation_router.post(
    "/orders/{order_id}/cancel-decline", response_model=OrderResponseSchema
)
async def decline_cancellation(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderCancellationUseCase = Depends(get_order_cancellation_use_case),
) -> OrderResponseSchema:
    return await _cancellation(use_case.decline, order_id, user)

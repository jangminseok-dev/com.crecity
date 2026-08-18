from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from order.adapter.inbound.api.schemas.order_result_schema import OrderResponseSchema
from order.app.dtos.order_progress_dto import OrderTransitionCommand
from order.app.dtos.order_result_dto import OrderResult
from order.app.exceptions import OrderNotFoundError
from order.app.ports.input.order_progress_use_case import OrderProgressUseCase
from order.dependencies.order_progress_provider import get_order_progress_use_case
from order.domain.entities.order_entity import InvalidOrderTransitionError, NotOrderActorError

order_progress_router = APIRouter(prefix="/order", tags=["order"])


async def _transition(
    action: Callable[[OrderTransitionCommand], Awaitable[OrderResult]],
    order_id: int,
    user: VerifiedUser,
) -> OrderResponseSchema:
    try:
        result = await action(OrderTransitionCommand(order_id=order_id, actor_user_id=user.id))
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderActorError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except InvalidOrderTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error))
    return OrderResponseSchema.from_result(result)


@order_progress_router.post("/orders/{order_id}/accept", response_model=OrderResponseSchema)
async def accept_order(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderProgressUseCase = Depends(get_order_progress_use_case),
) -> OrderResponseSchema:
    return await _transition(use_case.accept, order_id, user)


@order_progress_router.post("/orders/{order_id}/reject", response_model=OrderResponseSchema)
async def reject_order(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderProgressUseCase = Depends(get_order_progress_use_case),
) -> OrderResponseSchema:
    return await _transition(use_case.reject, order_id, user)


@order_progress_router.post(
    "/orders/{order_id}/submit-draft", response_model=OrderResponseSchema
)
async def submit_draft(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderProgressUseCase = Depends(get_order_progress_use_case),
) -> OrderResponseSchema:
    """초안 제출(갭 #85) — 게시 전 브랜드 컨펌을 받는 선택 단계."""
    return await _transition(use_case.submit_draft, order_id, user)


@order_progress_router.post(
    "/orders/{order_id}/approve-draft", response_model=OrderResponseSchema
)
async def approve_draft(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderProgressUseCase = Depends(get_order_progress_use_case),
) -> OrderResponseSchema:
    """초안 컨펌(갭 #85) — 크리에이터가 게시 작업을 이어간다."""
    return await _transition(use_case.approve_draft, order_id, user)


@order_progress_router.post("/orders/{order_id}/submit", response_model=OrderResponseSchema)
async def submit_order(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderProgressUseCase = Depends(get_order_progress_use_case),
) -> OrderResponseSchema:
    return await _transition(use_case.submit, order_id, user)


@order_progress_router.post(
    "/orders/{order_id}/request-revision", response_model=OrderResponseSchema
)
async def request_revision(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderProgressUseCase = Depends(get_order_progress_use_case),
) -> OrderResponseSchema:
    return await _transition(use_case.request_revision, order_id, user)


@order_progress_router.post("/orders/{order_id}/approve", response_model=OrderResponseSchema)
async def approve_order(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: OrderProgressUseCase = Depends(get_order_progress_use_case),
) -> OrderResponseSchema:
    return await _transition(use_case.approve, order_id, user)

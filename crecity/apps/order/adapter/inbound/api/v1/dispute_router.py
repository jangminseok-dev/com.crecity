from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from order.adapter.inbound.api.schemas.dispute_schema import (
    DisputeRequestSchema,
    DisputeResponseSchema,
)
from order.app.dtos.dispute_dto import DisputeListQuery, RaiseDisputeCommand
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.ports.input.dispute_use_case import DisputeUseCase
from order.dependencies.dispute_provider import get_dispute_use_case
from order.domain.entities.order_entity import InvalidOrderTransitionError, NotOrderActorError

dispute_router = APIRouter(prefix="/order", tags=["order"])


@dispute_router.post(
    "/orders/{order_id}/disputes", response_model=DisputeResponseSchema, status_code=201
)
async def raise_dispute(
    order_id: int,
    body: DisputeRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: DisputeUseCase = Depends(get_dispute_use_case),
) -> DisputeResponseSchema:
    try:
        result = await use_case.raise_dispute(
            RaiseDisputeCommand(
                order_id=order_id, actor_user_id=user.id, reason=body.reason
            )
        )
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderActorError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except InvalidOrderTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return DisputeResponseSchema.from_result(result)


@dispute_router.get(
    "/orders/{order_id}/disputes", response_model=list[DisputeResponseSchema]
)
async def list_disputes(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: DisputeUseCase = Depends(get_dispute_use_case),
) -> list[DisputeResponseSchema]:
    try:
        results = await use_case.list_disputes(
            DisputeListQuery(order_id=order_id, requester_user_id=user.id)
        )
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderParticipantError as error:
        raise HTTPException(status_code=403, detail=str(error))
    return [DisputeResponseSchema.from_result(result) for result in results]

from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from order.adapter.inbound.api.schemas.revision_lookup_schema import (
    RevisionRequestResponseSchema,
)
from order.app.dtos.revision_lookup_dto import RevisionListQuery
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.ports.input.revision_lookup_use_case import RevisionLookupUseCase
from order.dependencies.revision_lookup_provider import get_revision_lookup_use_case

revision_lookup_router = APIRouter(prefix="/order", tags=["order"])


@revision_lookup_router.get(
    "/orders/{order_id}/revisions", response_model=list[RevisionRequestResponseSchema]
)
async def list_revisions(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: RevisionLookupUseCase = Depends(get_revision_lookup_use_case),
) -> list[RevisionRequestResponseSchema]:
    """수정 요청 이력(갭 #84) — 당사자만. 어느 검토 단계의 피드백인지 함께 온다."""
    try:
        results = await use_case.list_revisions(
            RevisionListQuery(order_id=order_id, requester_user_id=user.id)
        )
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderParticipantError as error:
        raise HTTPException(status_code=403, detail=str(error))
    return [RevisionRequestResponseSchema.from_result(result) for result in results]

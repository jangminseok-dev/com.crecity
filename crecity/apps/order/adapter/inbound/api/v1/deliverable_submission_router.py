from fastapi import APIRouter, Depends, HTTPException, UploadFile

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from order.adapter.inbound.api.schemas.deliverable_submission_schema import (
    DeliverableLinkRequestSchema,
    DeliverableResponseSchema,
)
from order.app.dtos.deliverable_submission_dto import (
    DeliverableListQuery,
    SubmitDeliverableFileCommand,
    SubmitDeliverableLinkCommand,
)
from order.app.exceptions import NotOrderParticipantError, OrderNotFoundError
from order.app.ports.input.deliverable_submission_use_case import DeliverableSubmissionUseCase
from order.dependencies.deliverable_submission_provider import (
    get_deliverable_submission_use_case,
)
from order.domain.entities.order_entity import InvalidOrderTransitionError, NotOrderActorError

deliverable_submission_router = APIRouter(prefix="/order", tags=["order"])


@deliverable_submission_router.post(
    "/orders/{order_id}/deliverables/files",
    response_model=DeliverableResponseSchema,
    status_code=201,
)
async def submit_deliverable_file(
    order_id: int,
    file: UploadFile,
    user: VerifiedUser = Depends(get_current_user),
    use_case: DeliverableSubmissionUseCase = Depends(get_deliverable_submission_use_case),
) -> DeliverableResponseSchema:
    try:
        result = await use_case.submit_file(
            SubmitDeliverableFileCommand(
                order_id=order_id,
                actor_user_id=user.id,
                content=await file.read(),
                content_type=file.content_type or "",
                original_name=file.filename or "",
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
    return DeliverableResponseSchema.from_result(result)


@deliverable_submission_router.post(
    "/orders/{order_id}/deliverables/links",
    response_model=DeliverableResponseSchema,
    status_code=201,
)
async def submit_deliverable_link(
    order_id: int,
    body: DeliverableLinkRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: DeliverableSubmissionUseCase = Depends(get_deliverable_submission_use_case),
) -> DeliverableResponseSchema:
    try:
        result = await use_case.submit_link(
            SubmitDeliverableLinkCommand(
                order_id=order_id,
                actor_user_id=user.id,
                url=body.url,
                caption=body.caption,
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
    return DeliverableResponseSchema.from_result(result)


@deliverable_submission_router.get(
    "/orders/{order_id}/deliverables",
    response_model=list[DeliverableResponseSchema],
)
async def list_deliverables(
    order_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: DeliverableSubmissionUseCase = Depends(get_deliverable_submission_use_case),
) -> list[DeliverableResponseSchema]:
    try:
        results = await use_case.list_deliverables(
            DeliverableListQuery(order_id=order_id, requester_user_id=user.id)
        )
    except OrderNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotOrderParticipantError as error:
        raise HTTPException(status_code=403, detail=str(error))
    return [DeliverableResponseSchema.from_result(result) for result in results]

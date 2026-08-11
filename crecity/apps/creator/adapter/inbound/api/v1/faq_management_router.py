from fastapi import APIRouter, Depends, HTTPException, Response

from creator.adapter.inbound.api.schemas.faq_management_schema import (
    FaqRequestSchema,
    FaqResponseSchema,
)
from creator.app.dtos.faq_management_dto import AddFaqCommand, RemoveFaqCommand
from creator.app.exceptions import (
    FaqLimitExceededError,
    FaqNotFoundError,
    ProfileNotFoundError,
)
from creator.app.ports.input.faq_management_use_case import FaqManagementUseCase
from creator.dependencies.faq_management_provider import get_faq_management_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

faq_management_router = APIRouter(prefix="/creator", tags=["creator"])


@faq_management_router.post("/my/faqs", response_model=FaqResponseSchema, status_code=201)
async def add_faq(
    body: FaqRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: FaqManagementUseCase = Depends(get_faq_management_use_case),
) -> FaqResponseSchema:
    try:
        result = await use_case.add(
            AddFaqCommand(
                requester_user_id=user.id, question=body.question, answer=body.answer
            )
        )
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except FaqLimitExceededError as error:
        raise HTTPException(status_code=409, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return FaqResponseSchema.from_result(result)


@faq_management_router.get("/my/faqs", response_model=list[FaqResponseSchema])
async def list_my_faqs(
    user: VerifiedUser = Depends(get_current_user),
    use_case: FaqManagementUseCase = Depends(get_faq_management_use_case),
) -> list[FaqResponseSchema]:
    try:
        results = await use_case.list_mine(user.id)
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return [FaqResponseSchema.from_result(result) for result in results]


@faq_management_router.delete("/my/faqs/{faq_id}", status_code=204)
async def remove_faq(
    faq_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: FaqManagementUseCase = Depends(get_faq_management_use_case),
) -> Response:
    try:
        await use_case.remove(RemoveFaqCommand(requester_user_id=user.id, faq_id=faq_id))
    except (ProfileNotFoundError, FaqNotFoundError) as error:
        raise HTTPException(status_code=404, detail=str(error))
    return Response(status_code=204)


@faq_management_router.get("/profiles/{slug}/faqs", response_model=list[FaqResponseSchema])
async def list_profile_faqs(
    slug: str,
    use_case: FaqManagementUseCase = Depends(get_faq_management_use_case),
) -> list[FaqResponseSchema]:
    try:
        results = await use_case.list_public(slug)
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return [FaqResponseSchema.from_result(result) for result in results]

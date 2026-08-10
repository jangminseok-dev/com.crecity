from fastapi import APIRouter, Depends, HTTPException, UploadFile

from creator.adapter.inbound.api.schemas.portfolio_management_schema import (
    PortfolioItemResponseSchema,
)
from creator.app.dtos.portfolio_management_dto import (
    PortfolioListQuery,
    PortfolioRemovalCommand,
    PortfolioUploadCommand,
)
from creator.app.exceptions import (
    NotProfileOwnerError,
    PortfolioItemNotFoundError,
    PortfolioLimitExceededError,
    ProfileNotFoundError,
)
from creator.app.ports.input.portfolio_management_use_case import PortfolioManagementUseCase
from creator.dependencies.portfolio_management_provider import get_portfolio_management_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

portfolio_management_router = APIRouter(prefix="/creator", tags=["creator"])


def _to_schema(result) -> PortfolioItemResponseSchema:
    return PortfolioItemResponseSchema(
        id=result.id,
        image_url=f"/uploads/portfolio/{result.file_name}",
        created_at=result.created_at,
    )


@portfolio_management_router.post(
    "/my/portfolio", response_model=PortfolioItemResponseSchema, status_code=201
)
async def upload_portfolio_item(
    file: UploadFile,
    user: VerifiedUser = Depends(get_current_user),
    use_case: PortfolioManagementUseCase = Depends(get_portfolio_management_use_case),
) -> PortfolioItemResponseSchema:
    try:
        result = await use_case.upload(
            PortfolioUploadCommand(
                requester_user_id=user.id,
                content=await file.read(),
                content_type=file.content_type or "",
            )
        )
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except PortfolioLimitExceededError as error:
        raise HTTPException(status_code=409, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return _to_schema(result)


@portfolio_management_router.delete("/my/portfolio/{item_id}", status_code=204)
async def remove_portfolio_item(
    item_id: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: PortfolioManagementUseCase = Depends(get_portfolio_management_use_case),
) -> None:
    try:
        await use_case.remove(
            PortfolioRemovalCommand(item_id=item_id, requester_user_id=user.id)
        )
    except PortfolioItemNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotProfileOwnerError as error:
        raise HTTPException(status_code=403, detail=str(error))


@portfolio_management_router.get(
    "/profiles/{slug}/portfolio", response_model=list[PortfolioItemResponseSchema]
)
async def list_portfolio(
    slug: str,
    use_case: PortfolioManagementUseCase = Depends(get_portfolio_management_use_case),
) -> list[PortfolioItemResponseSchema]:
    try:
        results = await use_case.list_for_profile(PortfolioListQuery(slug=slug))
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return [_to_schema(result) for result in results]

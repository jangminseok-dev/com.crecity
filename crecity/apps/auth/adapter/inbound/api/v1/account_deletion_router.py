from fastapi import APIRouter, Depends, HTTPException, Response

from auth.adapter.inbound.api.schemas.account_deletion_schema import (
    AccountDeletionRequestSchema,
)
from auth.app.dtos.account_deletion_dto import DeleteAccountCommand
from auth.app.exceptions import (
    ActiveOrderExistsError,
    RemainingBalanceError,
    UserNotFoundError,
)
from auth.app.ports.input.account_deletion_use_case import AccountDeletionUseCase
from auth.dependencies.account_deletion_provider import get_account_deletion_use_case
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user

account_deletion_router = APIRouter(prefix="/auth", tags=["auth"])


@account_deletion_router.post("/account/delete", status_code=204)
async def delete_account(
    body: AccountDeletionRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: AccountDeletionUseCase = Depends(get_account_deletion_use_case),
) -> Response:
    try:
        await use_case.delete(
            DeleteAccountCommand(user_id=user.id, refresh_token=body.refresh_token or None)
        )
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except (ActiveOrderExistsError, RemainingBalanceError) as error:
        raise HTTPException(status_code=409, detail=str(error))
    return Response(status_code=204)

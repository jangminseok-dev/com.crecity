from fastapi import APIRouter, Depends, HTTPException

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from order.adapter.inbound.api.schemas.withdrawal_request_schema import (
    WithdrawalRequestSchema,
    WithdrawalResponseSchema,
)
from order.app.dtos.withdrawal_request_dto import WithdrawalRequestCommand, WithdrawalResult
from order.app.exceptions import InsufficientBalanceError, NotCreatorAccountError
from order.app.ports.input.withdrawal_request_use_case import WithdrawalRequestUseCase
from order.dependencies.withdrawal_request_provider import get_withdrawal_request_use_case

withdrawal_request_router = APIRouter(prefix="/order", tags=["order"])


def _to_schema(result: WithdrawalResult) -> WithdrawalResponseSchema:
    return WithdrawalResponseSchema(
        id=result.id,
        amount_krw=result.amount_krw,
        tax_krw=result.tax_krw,
        payout_krw=result.payout_krw,
        bank_name=result.bank_name,
        account_number=result.account_number,
        account_holder=result.account_holder,
        status=result.status,
        created_at=result.created_at,
        settled_at=result.settled_at,
    )


@withdrawal_request_router.post(
    "/withdrawals", response_model=WithdrawalResponseSchema, status_code=201
)
async def request_withdrawal(
    body: WithdrawalRequestSchema,
    user: VerifiedUser = Depends(get_current_user),
    use_case: WithdrawalRequestUseCase = Depends(get_withdrawal_request_use_case),
) -> WithdrawalResponseSchema:
    try:
        result = await use_case.request(
            WithdrawalRequestCommand(
                user_id=user.id,
                account_type=user.account_type,
                amount_krw=body.amount_krw,
                bank_name=body.bank_name,
                account_number=body.account_number,
                account_holder=body.account_holder,
            )
        )
    except NotCreatorAccountError as error:
        raise HTTPException(status_code=403, detail=str(error))
    except InsufficientBalanceError as error:
        raise HTTPException(status_code=409, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return _to_schema(result)


@withdrawal_request_router.get("/withdrawals", response_model=list[WithdrawalResponseSchema])
async def list_my_withdrawals(
    user: VerifiedUser = Depends(get_current_user),
    use_case: WithdrawalRequestUseCase = Depends(get_withdrawal_request_use_case),
) -> list[WithdrawalResponseSchema]:
    return [_to_schema(result) for result in await use_case.list_mine(user.id)]

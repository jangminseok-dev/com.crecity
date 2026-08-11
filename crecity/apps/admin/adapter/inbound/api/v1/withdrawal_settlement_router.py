from fastapi import APIRouter, Depends, HTTPException

from admin.adapter.inbound.api.schemas.withdrawal_settlement_schema import (
    WithdrawalSummarySchema,
)
from admin.app.dtos.withdrawal_settlement_dto import SettlementDecisionCommand
from admin.app.exceptions import SettlementTargetNotFoundError
from admin.app.ports.input.withdrawal_settlement_use_case import WithdrawalSettlementUseCase
from admin.dependencies.withdrawal_settlement_provider import (
    get_withdrawal_settlement_use_case,
)
from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.app.dtos.withdrawal_settlement_dto import WithdrawalSummary
from hub.dependencies.current_user_provider import require_permission

withdrawal_settlement_router = APIRouter(prefix="/admin", tags=["admin"])

_settler = require_permission("withdrawal.settle")


def _to_schema(summary: WithdrawalSummary) -> WithdrawalSummarySchema:
    return WithdrawalSummarySchema(
        id=summary.id,
        creator_user_id=summary.creator_user_id,
        amount_krw=summary.amount_krw,
        tax_krw=summary.tax_krw,
        payout_krw=summary.payout_krw,
        bank_name=summary.bank_name,
        account_number=summary.account_number,
        account_holder=summary.account_holder,
        status=summary.status,
        created_at=summary.created_at,
    )


@withdrawal_settlement_router.get(
    "/withdrawals/pending", response_model=list[WithdrawalSummarySchema]
)
async def list_pending_withdrawals(
    user: VerifiedUser = Depends(_settler),
    use_case: WithdrawalSettlementUseCase = Depends(get_withdrawal_settlement_use_case),
) -> list[WithdrawalSummarySchema]:
    return [_to_schema(summary) for summary in await use_case.list_pending()]


async def _settle(
    withdrawal_id: int,
    completed: bool,
    user: VerifiedUser,
    use_case: WithdrawalSettlementUseCase,
) -> WithdrawalSummarySchema:
    try:
        result = await use_case.settle(
            SettlementDecisionCommand(
                withdrawal_id=withdrawal_id,
                completed=completed,
                operator_id=user.id,
                operator_email=user.email,
            )
        )
    except SettlementTargetNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))
    return _to_schema(result)


@withdrawal_settlement_router.post(
    "/withdrawals/{withdrawal_id}/complete", response_model=WithdrawalSummarySchema
)
async def complete_withdrawal(
    withdrawal_id: int,
    user: VerifiedUser = Depends(_settler),
    use_case: WithdrawalSettlementUseCase = Depends(get_withdrawal_settlement_use_case),
) -> WithdrawalSummarySchema:
    return await _settle(withdrawal_id, completed=True, user=user, use_case=use_case)


@withdrawal_settlement_router.post(
    "/withdrawals/{withdrawal_id}/fail", response_model=WithdrawalSummarySchema
)
async def fail_withdrawal(
    withdrawal_id: int,
    user: VerifiedUser = Depends(_settler),
    use_case: WithdrawalSettlementUseCase = Depends(get_withdrawal_settlement_use_case),
) -> WithdrawalSummarySchema:
    return await _settle(withdrawal_id, completed=False, user=user, use_case=use_case)

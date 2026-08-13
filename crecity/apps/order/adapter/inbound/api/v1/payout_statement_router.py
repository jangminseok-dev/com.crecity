from fastapi import APIRouter, Depends

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from order.adapter.inbound.api.schemas.payout_statement_schema import PayoutStatementSchema
from order.app.dtos.payout_statement_dto import StatementQuery
from order.app.ports.input.payout_statement_use_case import PayoutStatementUseCase
from order.dependencies.payout_statement_provider import get_payout_statement_use_case

payout_statement_router = APIRouter(prefix="/order", tags=["order"])


@payout_statement_router.get(
    "/withdrawals/statements/{year}", response_model=PayoutStatementSchema
)
async def payout_statement(
    year: int,
    user: VerifiedUser = Depends(get_current_user),
    use_case: PayoutStatementUseCase = Depends(get_payout_statement_use_case),
) -> PayoutStatementSchema:
    """내 연간 지급명세서 — 남의 명세는 볼 수 없다(항상 본인 기준)."""
    result = await use_case.statement(StatementQuery(user_id=user.id, year=year))
    return PayoutStatementSchema.from_result(result)

from fastapi import APIRouter, Depends

from hub.app.dtos.verified_user_dto import VerifiedUser
from hub.dependencies.current_user_provider import get_current_user
from order.adapter.inbound.api.schemas.balance_lookup_schema import BalanceResponseSchema
from order.app.dtos.balance_lookup_dto import BalanceQuery
from order.app.ports.input.balance_lookup_use_case import BalanceLookupUseCase
from order.dependencies.balance_lookup_provider import get_balance_lookup_use_case

balance_lookup_router = APIRouter(prefix="/order", tags=["order"])


@balance_lookup_router.get("/balance", response_model=BalanceResponseSchema)
async def get_my_balance(
    user: VerifiedUser = Depends(get_current_user),
    use_case: BalanceLookupUseCase = Depends(get_balance_lookup_use_case),
) -> BalanceResponseSchema:
    result = await use_case.get_balance(BalanceQuery(user_id=user.id))
    return BalanceResponseSchema(user_id=result.user_id, balance_krw=result.balance_krw)

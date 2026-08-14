from fastapi import APIRouter, Depends

from order.adapter.inbound.api.schemas.fee_policy_schema import FeePolicyResponseSchema
from order.app.ports.input.fee_policy_use_case import FeePolicyUseCase
from order.dependencies.fee_policy_provider import get_fee_policy_use_case

fee_policy_router = APIRouter(prefix="/order", tags=["order"])


@fee_policy_router.get("/fee-policy", response_model=FeePolicyResponseSchema)
async def get_fee_policy(
    use_case: FeePolicyUseCase = Depends(get_fee_policy_use_case),
) -> FeePolicyResponseSchema:
    """현재 수수료·마감 정책(갭 #62) — **공개**. 입점 검토 중인 크리에이터도 봐야 한다."""
    return FeePolicyResponseSchema.from_result(use_case.get_policy())

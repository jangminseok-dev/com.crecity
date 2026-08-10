from fastapi import APIRouter, Depends

from payment.adapter.inbound.api.schemas.paymaster_schema import PaymasterResponseSchema
from payment.app.dtos.paymaster_dto import PaymasterQuery
from payment.app.ports.input.paymaster_use_case import PaymasterUseCase
from payment.dependencies.paymaster_provider import get_paymaster_use_case

paymaster_router = APIRouter(prefix="/payment", tags=["payment"])


@paymaster_router.get("/myself", response_model=PaymasterResponseSchema)
async def introduce_myself(
    paymaster: PaymasterUseCase = Depends(get_paymaster_use_case),
) -> PaymasterResponseSchema:
    result = await paymaster.introduce_myself(PaymasterQuery(id=6, name="결제 (payment)"))
    return PaymasterResponseSchema(
        id=result.id, name=result.name, introduction=result.introduction
    )

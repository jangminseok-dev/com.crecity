from fastapi import APIRouter, Depends

from creator.adapter.inbound.api.schemas.market_rates_schema import MarketRateItemSchema
from creator.app.ports.input.market_rates_use_case import MarketRatesUseCase
from creator.dependencies.market_rates_provider import get_market_rates_use_case

market_rates_router = APIRouter(prefix="/creator", tags=["creator"])


@market_rates_router.get("/market-rates", response_model=list[MarketRateItemSchema])
async def list_market_rates(
    use_case: MarketRatesUseCase = Depends(get_market_rates_use_case),
) -> list[MarketRateItemSchema]:
    """**공개** 실거래 시세(갭 #89) — 완료 주문 기반, 표본 미달 조합은 내지 않는다."""
    return [
        MarketRateItemSchema.from_item(item) for item in await use_case.list_market_rates()
    ]

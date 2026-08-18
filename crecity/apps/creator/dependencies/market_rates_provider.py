from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import MARKET_RATE_MIN_SAMPLES
from core.database import get_db
from creator.adapter.outbound.pg.creator_package_pg_repository import CreatorPackagePgRepository
from creator.app.ports.input.market_rates_use_case import MarketRatesUseCase
from creator.app.use_cases.market_rates_interactor import MarketRatesInteractor
from hub.dependencies.completed_order_price_provider import get_completed_order_price_port


def get_market_rates_use_case(
    db: AsyncSession = Depends(get_db),
) -> MarketRatesUseCase:
    return MarketRatesInteractor(
        packages=CreatorPackagePgRepository(session=db),
        completed_prices=get_completed_order_price_port(),
        min_samples=MARKET_RATE_MIN_SAMPLES,
    )

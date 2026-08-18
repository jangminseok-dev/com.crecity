from __future__ import annotations

from abc import ABC, abstractmethod

from creator.app.dtos.market_rates_dto import MarketRateItem


class MarketRatesUseCase(ABC):
    """실거래 시세 공개(갭 #89) — 완료 주문 기반 카테고리×플랫폼 요약."""

    @abstractmethod
    async def list_market_rates(self) -> list[MarketRateItem]: ...

from __future__ import annotations

from creator.app.dtos.market_rates_dto import MarketRateItem
from creator.app.ports.input.market_rates_use_case import MarketRatesUseCase
from creator.app.ports.output.creator_package_repository import CreatorPackageRepository
from creator.domain.value_objects.market_rate import MarketRateEntry, summarize_market_rates
from hub.app.ports.output.completed_order_price_port import CompletedOrderPricePort


class MarketRatesInteractor(MarketRatesUseCase):

    def __init__(
        self,
        packages: CreatorPackageRepository,
        completed_prices: CompletedOrderPricePort,
        min_samples: int,
    ) -> None:
        self._packages = packages
        self._completed_prices = completed_prices
        self._min_samples = min_samples

    async def list_market_rates(self) -> list[MarketRateItem]:
        # 거래가는 order 소유라 허브 계약으로 읽고, 분류(카테고리·플랫폼)는 여기 데이터로 해석한다
        amounts = await self._completed_prices.list_completed_package_amounts()
        if not amounts:
            return []
        classification = await self._packages.classify_by_package_ids(
            list({a.package_id for a in amounts})
        )
        # 패키지가 삭제돼 분류할 수 없는 거래는 제외한다(어느 조합에도 넣을 근거가 없다)
        entries = [
            MarketRateEntry(
                category=classification[a.package_id][0],
                platform=classification[a.package_id][1],
                amount_krw=a.amount_krw,
            )
            for a in amounts
            if a.package_id in classification
        ]
        return [
            MarketRateItem(
                category=rate.category,
                platform=rate.platform,
                sample_count=rate.sample_count,
                median_krw=rate.median_krw,
                p25_krw=rate.p25_krw,
                p75_krw=rate.p75_krw,
            )
            for rate in summarize_market_rates(entries, min_samples=self._min_samples)
        ]

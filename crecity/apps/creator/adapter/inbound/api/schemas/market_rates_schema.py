from __future__ import annotations

from pydantic import BaseModel

from creator.app.dtos.market_rates_dto import MarketRateItem


class MarketRateItemSchema(BaseModel):
    """카테고리×플랫폼 실거래 시세 1행(갭 #89) — 중앙값·사분위 범위·표본 수."""

    category: str
    platform: str
    sample_count: int
    median_krw: int
    p25_krw: int
    p75_krw: int

    @classmethod
    def from_item(cls, item: MarketRateItem) -> MarketRateItemSchema:
        return cls(
            category=item.category,
            platform=item.platform,
            sample_count=item.sample_count,
            median_krw=item.median_krw,
            p25_krw=item.p25_krw,
            p75_krw=item.p75_krw,
        )

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketRateItem:
    """카테고리×플랫폼 시세 요약 1행 — 중앙값·사분위 범위·표본 수."""

    category: str
    platform: str
    sample_count: int
    median_krw: int
    p25_krw: int
    p75_krw: int

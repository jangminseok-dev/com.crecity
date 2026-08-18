"""실거래 시세 집계(갭 #89) — 완료 주문 거래가를 카테고리×플랫폼으로 요약한다.

평균 대신 **중앙값 + 사분위 범위(p25~p75)**를 쓴다 — 거래가 분포는 꼬리가 길어
평균이 큰 거래 몇 건에 끌려간다. 표본이 min_samples 미만인 조합은 아예 내지 않는다
(소표본 시세는 특정 거래 가격 역추정·왜곡된 참고치가 된다 — 기준값은 core/config 소유).
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median, quantiles


@dataclass(frozen=True)
class MarketRateEntry:
    category: str
    platform: str
    amount_krw: int


@dataclass(frozen=True)
class MarketRate:
    category: str
    platform: str
    sample_count: int
    median_krw: int
    p25_krw: int
    p75_krw: int


def summarize_market_rates(
    entries: list[MarketRateEntry], min_samples: int
) -> list[MarketRate]:
    groups: dict[tuple[str, str], list[int]] = {}
    for entry in entries:
        groups.setdefault((entry.category, entry.platform), []).append(entry.amount_krw)

    rates = []
    for (category, platform), amounts in groups.items():
        if len(amounts) < min_samples:
            continue
        q1, _, q3 = quantiles(amounts, n=4, method="inclusive")
        rates.append(
            MarketRate(
                category=category,
                platform=platform,
                sample_count=len(amounts),
                median_krw=int(median(amounts)),
                p25_krw=int(q1),
                p75_krw=int(q3),
            )
        )
    return sorted(rates, key=lambda r: (r.category, r.platform))

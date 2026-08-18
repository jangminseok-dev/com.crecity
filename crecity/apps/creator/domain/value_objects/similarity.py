"""유사 크리에이터 순위 규칙(갭 #88) — 카테고리·가격대·플랫폼 기반, LLM 없는 규칙 추천.

후보는 이미 같은 카테고리(+승인·주문 수신 중)로 좁혀져 들어온다. 여기서는
① 타깃과 패키지 플랫폼이 하나라도 겹치는 프로필 우선
② 최저가가 타깃 최저가에 가까운 순(가격 없는 프로필은 뒤로)
③ 동률이면 최신 프로필 우선
으로 줄 세운다. 타깃에 최저가가 없으면 가격 근접성은 판단하지 않는다(전원 동률).
"""

from __future__ import annotations

from dataclasses import dataclass

_NO_PRICE = float("inf")  # 가격 없는 후보는 가격 비교에서 항상 뒤


@dataclass(frozen=True)
class SimilarityCandidate:
    profile_id: int
    min_price: int | None
    platforms: frozenset[str]


def rank_similar(
    target_price: int | None,
    target_platforms: frozenset[str],
    candidates: list[SimilarityCandidate],
    limit: int,
) -> list[int]:
    def sort_key(candidate: SimilarityCandidate) -> tuple:
        platform_miss = 0 if target_platforms & candidate.platforms else 1
        if target_price is None:
            price_gap = 0.0  # 타깃 가격이 없으면 근거 없는 가격 비교를 하지 않는다
        elif candidate.min_price is None:
            price_gap = _NO_PRICE
        else:
            price_gap = float(abs(candidate.min_price - target_price))
        return (platform_miss, price_gap, -candidate.profile_id)

    return [c.profile_id for c in sorted(candidates, key=sort_key)[:limit]]

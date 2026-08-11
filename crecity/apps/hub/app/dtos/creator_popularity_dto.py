from dataclasses import dataclass


@dataclass(frozen=True)
class CreatorOrderCount:
    """최근 주문 수 기준 크리에이터 순위 항목.

    score = order_count − expired_count × 페널티 가중치(§3.8 무응답 페널티) — 정렬 기준.
    """

    creator_user_id: int
    order_count: int
    expired_count: int = 0
    score: int = 0

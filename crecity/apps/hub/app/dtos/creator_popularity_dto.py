from dataclasses import dataclass


@dataclass(frozen=True)
class CreatorOrderCount:
    """최근 주문 수 기준 크리에이터 순위 항목."""

    creator_user_id: int
    order_count: int

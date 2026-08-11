from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from order.domain.entities.order_adjustment_entity import OrderAdjustment


@dataclass(frozen=True)
class RequestAdjustmentCommand:

    order_id: int
    actor_user_id: int  # 크리에이터만
    extra_amount_krw: int
    reason: str


@dataclass(frozen=True)
class DeclineAdjustmentCommand:

    adjustment_id: int
    actor_user_id: int  # 브랜드만


@dataclass(frozen=True)
class AdjustmentListQuery:

    order_id: int
    requester_user_id: int  # 당사자만


@dataclass(frozen=True)
class AdjustmentResult:

    id: int
    order_id: int
    extra_amount_krw: int
    reason: str
    status: str
    created_at: datetime | None

    @classmethod
    def from_entity(cls, adjustment: OrderAdjustment) -> AdjustmentResult:
        return cls(
            id=adjustment.id,
            order_id=adjustment.order_id,
            extra_amount_krw=adjustment.extra_amount_krw,
            reason=adjustment.reason,
            status=adjustment.status.value,
            created_at=adjustment.created_at,
        )

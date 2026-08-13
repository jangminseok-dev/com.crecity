from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from order.domain.entities.dispute_entity import Dispute


@dataclass(frozen=True)
class RaiseDisputeCommand:
    order_id: int
    actor_user_id: int
    reason: str


@dataclass(frozen=True)
class DisputeListQuery:
    order_id: int
    requester_user_id: int


@dataclass(frozen=True)
class DisputeResult:
    id: int
    order_id: int
    raised_by_user_id: int
    reason: str
    status: str
    resolution: str | None
    created_at: datetime | None
    resolved_at: datetime | None

    @classmethod
    def from_dispute(cls, dispute: Dispute) -> DisputeResult:
        return cls(
            id=dispute.id,
            order_id=dispute.order_id,
            raised_by_user_id=dispute.raised_by_user_id,
            reason=dispute.reason,
            status=dispute.status.value,
            resolution=dispute.resolution.value if dispute.resolution else None,
            created_at=dispute.created_at,
            resolved_at=dispute.resolved_at,
        )

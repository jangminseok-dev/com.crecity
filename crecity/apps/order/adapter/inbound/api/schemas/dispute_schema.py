from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from order.app.dtos.dispute_dto import DisputeResult


class DisputeRequestSchema(BaseModel):
    reason: str


class DisputeResponseSchema(BaseModel):
    id: int
    order_id: int
    raised_by_user_id: int
    reason: str
    status: str  # OPEN | RESOLVED
    resolution: str | None  # REFUND | RELEASE | DISMISS — 판정 전에는 null
    created_at: datetime | None
    resolved_at: datetime | None

    @classmethod
    def from_result(cls, result: DisputeResult) -> DisputeResponseSchema:
        return cls(
            id=result.id,
            order_id=result.order_id,
            raised_by_user_id=result.raised_by_user_id,
            reason=result.reason,
            status=result.status,
            resolution=result.resolution,
            created_at=result.created_at,
            resolved_at=result.resolved_at,
        )

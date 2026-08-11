from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from order.app.dtos.order_adjustment_dto import AdjustmentResult


class AdjustmentRequestSchema(BaseModel):

    extra_amount_krw: int = Field(..., gt=0, description="추가 금액(원)")
    reason: str = Field(..., max_length=500, description="추가 작업 범위·사유")


class AdjustmentResponseSchema(BaseModel):

    id: int
    order_id: int
    extra_amount_krw: int
    reason: str
    status: str  # REQUESTED | PAID | DECLINED
    created_at: datetime | None

    @classmethod
    def from_result(cls, result: AdjustmentResult) -> AdjustmentResponseSchema:
        return cls(
            id=result.id,
            order_id=result.order_id,
            extra_amount_krw=result.extra_amount_krw,
            reason=result.reason,
            status=result.status,
            created_at=result.created_at,
        )

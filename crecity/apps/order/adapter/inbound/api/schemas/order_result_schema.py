from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from order.app.dtos.order_result_dto import OrderResult


class OrderResponseSchema(BaseModel):
    """주문 공용 응답 — placement·progress·lookup 라우터가 공유한다(도메인어 명명 예외)."""

    id: int
    package_id: int | None
    package_title: str
    brand_user_id: int
    creator_user_id: int
    amount_krw: int
    brand_total_krw: int
    creator_payout_krw: int
    brand_fee_percent: int
    creator_fee_percent: int
    requirements: str
    status: str
    deadline_at: datetime | None
    cancel_requested_by: int | None
    created_at: datetime | None

    @classmethod
    def from_result(cls, result: OrderResult) -> OrderResponseSchema:
        return cls(
            id=result.id,
            package_id=result.package_id,
            package_title=result.package_title,
            brand_user_id=result.brand_user_id,
            creator_user_id=result.creator_user_id,
            amount_krw=result.amount_krw,
            brand_total_krw=result.brand_total_krw,
            creator_payout_krw=result.creator_payout_krw,
            brand_fee_percent=result.brand_fee_percent,
            creator_fee_percent=result.creator_fee_percent,
            requirements=result.requirements,
            status=result.status,
            deadline_at=result.deadline_at,
            cancel_requested_by=result.cancel_requested_by,
            created_at=result.created_at,
        )

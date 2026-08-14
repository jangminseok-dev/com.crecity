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
    revision_limit: int
    revisions_used: int
    usage_rights: str
    created_at: datetime | None
    # 조회 요청자 기준 거래 상대(갭 #63)
    counterpart_name: str | None = None
    counterpart_slug: str | None = None
    # 상대의 거래 이력(갭 #65·#66) — 이력이 없으면 null
    counterpart_completed_orders: int | None = None
    counterpart_cancelled_orders: int | None = None
    counterpart_accept_expired_orders: int | None = None
    counterpart_total_revisions: int | None = None

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
            revision_limit=result.revision_limit,
            revisions_used=result.revisions_used,
            usage_rights=result.usage_rights,
            created_at=result.created_at,
            counterpart_name=result.counterpart_name,
            counterpart_slug=result.counterpart_slug,
            counterpart_completed_orders=result.counterpart_completed_orders,
            counterpart_cancelled_orders=result.counterpart_cancelled_orders,
            counterpart_accept_expired_orders=result.counterpart_accept_expired_orders,
            counterpart_total_revisions=result.counterpart_total_revisions,
        )

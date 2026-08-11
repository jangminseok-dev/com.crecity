from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from order.domain.entities.order_entity import Order


@dataclass(frozen=True)
class OrderResult:
    """주문 응답 DTO — placement·progress·lookup 슬라이스가 공유한다(도메인어 명명 예외)."""

    id: int
    package_id: int | None
    package_title: str
    brand_user_id: int
    creator_user_id: int
    amount_krw: int
    brand_total_krw: int  # 브랜드 결제 총액(수수료 포함 — 에스크로 예치액)
    creator_payout_krw: int  # 구매 확정 시 크리에이터 적립액
    brand_fee_percent: int
    creator_fee_percent: int
    requirements: str
    status: str
    deadline_at: datetime | None
    cancel_requested_by: int | None
    created_at: datetime | None

    @classmethod
    def from_order(cls, order: Order) -> OrderResult:
        return cls(
            id=order.id,
            package_id=order.package_id,
            package_title=order.package_title,
            brand_user_id=order.brand_user_id,
            creator_user_id=order.creator_user_id,
            amount_krw=order.amount_krw,
            brand_total_krw=order.brand_total_krw(),
            creator_payout_krw=order.creator_payout_krw(),
            brand_fee_percent=order.brand_fee_percent,
            creator_fee_percent=order.creator_fee_percent,
            requirements=order.requirements,
            status=order.status.value,
            deadline_at=order.deadline_at,
            cancel_requested_by=order.cancel_requested_by,
            created_at=order.created_at,
        )

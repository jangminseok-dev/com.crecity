from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from admin.app.dtos.order_search_dto import OrderSearchItem, OrderSearchResultDto


class AdminOrderSchema(BaseModel):

    id: int
    package_title: str
    brand_user_id: int
    creator_user_id: int
    amount_krw: int
    status: str
    accept_expired: bool
    cancel_requested_by: int | None
    revisions_used: int
    revision_limit: int
    deadline_at: datetime | None
    created_at: datetime | None

    @classmethod
    def from_item(cls, item: OrderSearchItem) -> AdminOrderSchema:
        return cls(
            id=item.id,
            package_title=item.package_title,
            brand_user_id=item.brand_user_id,
            creator_user_id=item.creator_user_id,
            amount_krw=item.amount_krw,
            status=item.status,
            accept_expired=item.accept_expired,
            cancel_requested_by=item.cancel_requested_by,
            revisions_used=item.revisions_used,
            revision_limit=item.revision_limit,
            deadline_at=item.deadline_at,
            created_at=item.created_at,
        )


class AdminOrderSearchResponseSchema(BaseModel):

    items: list[AdminOrderSchema]
    total: int

    @classmethod
    def from_result(cls, result: OrderSearchResultDto) -> AdminOrderSearchResponseSchema:
        return cls(
            items=[AdminOrderSchema.from_item(item) for item in result.items],
            total=result.total,
        )

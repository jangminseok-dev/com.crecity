from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OrderSearchQuery:
    """운영자가 넣은 검색 조건 — 라우터 스키마가 아니라 이 DTO로 유스케이스에 넘긴다."""

    order_id: int | None = None
    status: str | None = None
    user_id: int | None = None
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class OrderSearchItem:

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


@dataclass(frozen=True)
class OrderSearchResultDto:

    items: list[OrderSearchItem]
    total: int

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OrderSearchCriteria:
    """운영 주문 검색 조건 — 값이 있는 것만 AND로 걸린다."""

    order_id: int | None = None
    status: str | None = None
    user_id: int | None = None  # 브랜드·크리에이터 어느 쪽으로든 참여한 주문
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class AdminOrderSummary:
    """운영 조회용 주문 요약 — 분쟁 판정 화면과 같은 수준의 정보를 싣는다."""

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
class OrderSearchResult:
    """목록 + 총계 — 총계는 목록과 같은 조건으로 센다."""

    items: list[AdminOrderSummary]
    total: int

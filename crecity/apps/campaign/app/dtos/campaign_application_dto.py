from dataclasses import dataclass

from campaign.domain.value_objects.application_sort import ApplicationSort
from datetime import datetime


@dataclass(frozen=True)
class ApplyCommand:

    campaign_id: int
    creator_user_id: int  # 로그인 사용자
    account_type: str  # CREATOR만
    message: str
    proposed_price_krw: int


@dataclass(frozen=True)
class ApplicationsQuery:
    """지원자 조회 — 정렬·필터는 갭 #70."""

    campaign_id: int
    requester_user_id: int  # 공고 브랜드만 열람
    sort: ApplicationSort = ApplicationSort.OLDEST
    only_open: bool = False  # 아직 수락하지 않은 지원만


@dataclass(frozen=True)
class ApplicationResult:

    id: int
    campaign_id: int
    creator_user_id: int
    creator_name: str  # 허브 CreatorRefPort로 실시간 해석(스냅샷 아님 — 3NF)
    creator_slug: str
    message: str
    proposed_price_krw: int
    order_id: int | None  # 수락(결제)된 지원이면 생성된 주문 id
    created_at: datetime | None

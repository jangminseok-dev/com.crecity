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
class MyApplicationsQuery:
    """크리에이터 본인의 지원 내역 조회(갭 #103)."""

    creator_user_id: int
    account_type: str  # CREATOR만


@dataclass(frozen=True)
class MyApplicationResult:
    """내 지원 1건 — 공고 정보를 함께 실어 상태를 화면에서 파생한다(갭 #103).

    지원 상태는 별도 컬럼이 아니라 `order_id`(선정)와 공고 상태·마감일(마감)에서
    나온다 — 같은 사실을 두 곳에 두지 않는다.
    """

    id: int
    campaign_id: int
    campaign_title: str
    campaign_status: str  # OPEN | CLOSED
    campaign_deadline_at: datetime | None
    message: str
    proposed_price_krw: int
    order_id: int | None  # 선정(결제)되면 생성된 주문 id
    created_at: datetime | None


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

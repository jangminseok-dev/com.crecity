from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProfileLookupQuery:

    slug: str


@dataclass(frozen=True)
class ProfileLookupResult:

    id: int
    slug: str
    name: str
    tagline: str
    bio: str
    location: str | None
    primary_category: str
    status: str
    created_at: datetime | None
    followers_total: int = 0  # 전 채널 팔로워 합(자가입력 기준) — 헤더 배지(§2.1-2)
    accepting_orders: bool = True  # 주문 수신 여부(갭 #64) — 구매 버튼 노출 판단
    # 거래 실적(갭 #66) — 받은 주문이 없으면 None(0건을 보여 신규를 깎지 않는다)
    completed_orders: int | None = None
    accepted_orders: int | None = None
    received_orders: int | None = None

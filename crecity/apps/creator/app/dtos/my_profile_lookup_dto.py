from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MyProfileQuery:

    user_id: int


@dataclass(frozen=True)
class MyProfileResult:

    id: int
    slug: str
    name: str
    tagline: str
    bio: str
    location: str | None
    primary_category: str
    status: str
    created_at: datetime | None
    accepting_orders: bool = True  # 주문 수신 여부(갭 #64) — 대시보드 토글이 읽는다
    rejection_reason: str | None = None  # 반려 사유(갭 #101) — REJECTED일 때만 값이 있다

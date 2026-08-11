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

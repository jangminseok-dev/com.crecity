from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProfileRegistrationCommand:

    slug: str
    name: str
    tagline: str
    bio: str
    location: str | None
    primary_category: str
    user_id: int  # 로그인 사용자 (허브 계약으로 검증됨)
    account_type: str  # CREATOR만 등록 가능


@dataclass(frozen=True)
class ProfileRegistrationResult:

    id: int
    slug: str
    name: str
    tagline: str
    bio: str
    location: str | None
    primary_category: str
    status: str
    created_at: datetime | None

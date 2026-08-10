from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PackageRegistrationCommand:

    slug: str  # 소속 프로필
    platform: str
    title: str
    description: str
    price_krw: int
    requester_user_id: int  # 로그인 사용자 — 프로필 소유자만 등록 가능


@dataclass(frozen=True)
class PackageUpdateCommand:

    package_id: int
    platform: str
    title: str
    description: str
    price_krw: int
    requester_user_id: int


@dataclass(frozen=True)
class PackageRemovalCommand:

    package_id: int
    requester_user_id: int


@dataclass(frozen=True)
class PackageListQuery:

    slug: str


@dataclass(frozen=True)
class PackageResult:

    id: int
    profile_id: int
    platform: str
    title: str
    description: str
    price_krw: int
    created_at: datetime | None

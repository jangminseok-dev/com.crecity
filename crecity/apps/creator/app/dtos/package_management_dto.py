from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PackageRegistrationCommand:

    slug: str  # 소속 프로필
    platform: str
    title: str
    description: str
    price_krw: int


@dataclass(frozen=True)
class PackageUpdateCommand:

    package_id: int
    platform: str
    title: str
    description: str
    price_krw: int


@dataclass(frozen=True)
class PackageRemovalCommand:

    package_id: int


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

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PortfolioUploadCommand:

    requester_user_id: int  # 내 프로필에만 업로드
    content: bytes
    content_type: str


@dataclass(frozen=True)
class PortfolioRemovalCommand:

    item_id: int
    requester_user_id: int


@dataclass(frozen=True)
class PortfolioListQuery:

    slug: str


@dataclass(frozen=True)
class PortfolioItemResult:

    id: int
    profile_id: int
    file_name: str
    created_at: datetime | None

from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileUpdateCommand:
    """내 프로필 수정 — 슬러그는 SEO 단위(공개 URL)라 변경 불가."""

    user_id: int
    name: str
    tagline: str
    bio: str
    location: str | None
    primary_category: str

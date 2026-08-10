from pydantic import BaseModel, Field


class ProfileUpdateRequestSchema(BaseModel):
    """슬러그는 공개 URL(SEO 단위)이라 수정 불가 — 내용 필드만 받는다."""

    name: str = Field(..., min_length=1, max_length=100)
    tagline: str = Field(..., min_length=1, max_length=200)
    bio: str = Field(..., min_length=1)
    location: str | None = Field(None, max_length=100)
    primary_category: str = Field(..., min_length=1, max_length=50)

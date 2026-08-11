from datetime import datetime

from pydantic import BaseModel, Field


class PostCampaignRequestSchema(BaseModel):

    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, description="원하는 콘텐츠·조건·기간 등")
    platform: str = Field(..., description="INSTAGRAM | YOUTUBE | TIKTOK | NAVER_BLOG | UGC")
    budget_krw: int = Field(..., description="예산 상한(원)")
    deadline_at: datetime | None = Field(None, description="지원 마감일(선택) — 경과 시 자동 마감")
    target_category: str | None = Field(None, max_length=50, description="타겟 니치(선택)")
    target_location: str | None = Field(None, max_length=100, description="타겟 지역(선택)")


class CampaignResponseSchema(BaseModel):

    id: int
    brand_user_id: int
    title: str
    description: str
    platform: str
    budget_krw: int
    status: str
    deadline_at: datetime | None
    target_category: str | None
    target_location: str | None
    created_at: datetime | None

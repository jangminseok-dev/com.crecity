from datetime import datetime

from pydantic import BaseModel, Field


class PostCampaignRequestSchema(BaseModel):

    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, description="원하는 콘텐츠·조건·기간 등")
    platform: str = Field(..., description="INSTAGRAM | YOUTUBE | TIKTOK | NAVER_BLOG | UGC")
    budget_krw: int = Field(..., description="예산 상한(원)")


class CampaignResponseSchema(BaseModel):

    id: int
    brand_user_id: int
    title: str
    description: str
    platform: str
    budget_krw: int
    status: str
    created_at: datetime | None

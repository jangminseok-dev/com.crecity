from datetime import datetime

from pydantic import BaseModel, Field


class PackageWriteRequestSchema(BaseModel):
    """등록·수정 공용 요청 본문 (소속 프로필·패키지 id는 경로에서)."""

    platform: str = Field(..., description="INSTAGRAM | YOUTUBE | TIKTOK | NAVER_BLOG | UGC")
    title: str = Field(..., max_length=100)
    description: str = Field(..., description="납품물·수정 횟수 등 상세")
    price_krw: int = Field(..., description="판매가(원)")
    revision_limit: int = Field(2, ge=0, le=10, description="수정 요청 허용 횟수(§3.3)")
    usage_rights: str = Field("", max_length=300, description="2차 활용 범위(§9.2)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "platform": "INSTAGRAM",
                "title": "인스타그램 릴스 1개",
                "description": "60초 이내 릴스 1건 제작·게시, 수정 2회 포함",
                "price_krw": 300000,
                "revision_limit": 2,
                "usage_rights": "SNS 게시 6개월, 유료 광고 별도 협의",
            }
        }
    }


class PackageResponseSchema(BaseModel):

    id: int
    profile_id: int
    platform: str
    title: str
    description: str
    price_krw: int
    revision_limit: int
    usage_rights: str
    created_at: datetime | None

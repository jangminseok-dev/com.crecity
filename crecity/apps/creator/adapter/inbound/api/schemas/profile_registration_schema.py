from datetime import datetime

from pydantic import BaseModel, Field


class ProfileRegistrationRequestSchema(BaseModel):

    slug: str = Field(..., max_length=30, description="공개 URL 슬러그 (소문자·숫자·하이픈)")
    name: str = Field(..., max_length=100)
    tagline: str = Field(..., max_length=200, description="한 줄 포지셔닝")
    bio: str = Field(..., description="자기소개")
    location: str | None = Field(None, max_length=100)
    primary_category: str = Field(..., max_length=50, description="니치 카테고리")

    model_config = {
        "json_schema_extra": {
            "example": {
                "slug": "kim-beauty",
                "name": "김뷰티",
                "tagline": "20대 스킨케어·K뷰티 리뷰",
                "bio": "스킨케어 성분 분석 콘텐츠를 만듭니다.",
                "location": "서울",
                "primary_category": "뷰티",
            }
        }
    }


class ProfileRegistrationResponseSchema(BaseModel):

    id: int
    slug: str
    name: str
    tagline: str
    bio: str
    location: str | None
    primary_category: str
    status: str
    created_at: datetime | None

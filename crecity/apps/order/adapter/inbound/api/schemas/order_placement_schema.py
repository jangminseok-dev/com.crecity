from pydantic import BaseModel, Field


class OrderPlacementRequestSchema(BaseModel):

    package_id: int
    requirements: str = Field(..., description="브랜드 요구사항 — 수정 요청 범위의 기준")

    model_config = {
        "json_schema_extra": {
            "example": {
                "package_id": 1,
                "requirements": "신제품 클렌저 소개 60초 릴스, 성분 강조, 8/20까지 게시",
            }
        }
    }

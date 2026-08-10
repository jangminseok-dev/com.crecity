from pydantic import BaseModel, Field


class ProfileSchema(BaseModel):

    id: int = Field(0, description="Agent ID")
    name: str = Field("크리에이터 (creator)", description="담당 이름")
    # 크리에이터 프로필·판매 패키지 — 마켓플레이스 공급 측 상품 단위

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 3,
                "name": "크리에이터 (creator)",
            }
        }
    }


class ProfileResponseSchema(BaseModel):

    id: int
    name: str
    introduction: str

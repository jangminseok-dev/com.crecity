from pydantic import BaseModel, Field


class GatekeeperSchema(BaseModel):

    id: int = Field(0, description="Agent ID")
    name: str = Field("인증 (auth)", description="담당 이름")
    # 회원 인증·계정 — 크리에이터/브랜드 계정 경계 담당

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 2,
                "name": "인증 (auth)",
            }
        }
    }


class GatekeeperResponseSchema(BaseModel):

    id: int
    name: str
    introduction: str

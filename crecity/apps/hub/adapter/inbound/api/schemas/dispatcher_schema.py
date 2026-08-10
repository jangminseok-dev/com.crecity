from pydantic import BaseModel, Field


class DispatcherSchema(BaseModel):

    id: int = Field(0, description="Agent ID")
    name: str = Field("허브 (hub)", description="담당 이름")
    # 앱 간 협력의 단일 교차점 — 계약(포트·DTO)만 소유

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "허브 (hub)",
            }
        }
    }


class DispatcherResponseSchema(BaseModel):

    id: int
    name: str
    introduction: str

from pydantic import BaseModel, Field


class LogoutRequestSchema(BaseModel):

    refresh_token: str = Field(..., description="폐기할 리프레시 토큰 — BFF가 쿠키에서 꺼내 전달")

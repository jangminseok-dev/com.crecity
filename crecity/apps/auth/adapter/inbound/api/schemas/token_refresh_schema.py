from pydantic import BaseModel, Field


class TokenRefreshRequestSchema(BaseModel):

    refresh_token: str = Field(..., description="로그인/갱신 때 받은 리프레시 토큰(1회용)")


class TokenRefreshResponseSchema(BaseModel):

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

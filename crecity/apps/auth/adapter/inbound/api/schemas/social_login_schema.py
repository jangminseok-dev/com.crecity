from typing import Literal

from pydantic import BaseModel, Field


class AuthorizeUrlResponseSchema(BaseModel):

    authorize_url: str


class SocialLoginRequestSchema(BaseModel):

    code: str = Field(..., description="제공자 콜백으로 받은 인가 코드")
    redirect_uri: str = Field(..., description="인가 요청에 사용한 redirect_uri와 동일해야 함")
    state: str = Field("", description="인가 요청에 보낸 state (네이버는 토큰 교환에도 필수)")
    account_type: Literal["CREATOR", "BRAND"] = Field(
        ..., description="신규 가입 시 계정 유형 — 기존 계정 로그인이면 무시됨"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "abc123",
                "redirect_uri": "http://localhost:3000/oauth/kakao/callback",
                "state": "random-csrf-token",
                "account_type": "CREATOR",
            }
        }
    }


class AuthenticatedUserSchema(BaseModel):

    id: int
    email: str
    name: str
    account_type: str


class SocialLoginResponseSchema(BaseModel):

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool
    user: AuthenticatedUserSchema

from pydantic import BaseModel, Field


class AccountDeletionRequestSchema(BaseModel):

    refresh_token: str = Field(
        "", description="함께 폐기할 리프레시 토큰 — BFF가 쿠키에서 꺼내 전달"
    )

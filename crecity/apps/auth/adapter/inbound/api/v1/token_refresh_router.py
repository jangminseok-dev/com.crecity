from fastapi import APIRouter, Depends, HTTPException

from auth.adapter.inbound.api.schemas.token_refresh_schema import (
    TokenRefreshRequestSchema,
    TokenRefreshResponseSchema,
)
from auth.app.dtos.token_refresh_dto import TokenRefreshCommand
from auth.app.exceptions import InvalidRefreshTokenError
from auth.app.ports.input.token_refresh_use_case import TokenRefreshUseCase
from auth.dependencies.token_refresh_provider import get_token_refresh_use_case

token_refresh_router = APIRouter(prefix="/auth", tags=["auth"])


@token_refresh_router.post("/tokens/refresh", response_model=TokenRefreshResponseSchema)
async def refresh_tokens(
    body: TokenRefreshRequestSchema,
    use_case: TokenRefreshUseCase = Depends(get_token_refresh_use_case),
) -> TokenRefreshResponseSchema:
    try:
        result = await use_case.refresh(TokenRefreshCommand(refresh_token=body.refresh_token))
    except InvalidRefreshTokenError as error:
        raise HTTPException(status_code=401, detail=str(error))
    return TokenRefreshResponseSchema(
        access_token=result.access_token, refresh_token=result.refresh_token
    )

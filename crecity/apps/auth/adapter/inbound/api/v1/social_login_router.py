from fastapi import APIRouter, Depends, HTTPException, Query

from auth.adapter.inbound.api.schemas.social_login_schema import (
    AuthenticatedUserSchema,
    AuthorizeUrlResponseSchema,
    SocialLoginRequestSchema,
    SocialLoginResponseSchema,
)
from auth.app.dtos.social_login_dto import AuthorizeUrlQuery, SocialLoginCommand
from auth.app.exceptions import (
    EmailNotProvidedError,
    OAuthExchangeError,
    UnsupportedProviderError,
)
from auth.app.ports.input.social_login_use_case import SocialLoginUseCase
from auth.dependencies.social_login_provider import get_social_login_use_case

social_login_router = APIRouter(prefix="/auth", tags=["auth"])


@social_login_router.get(
    "/social/{provider}/authorize-url", response_model=AuthorizeUrlResponseSchema
)
async def get_authorize_url(
    provider: str,
    redirect_uri: str = Query(..., description="제공자 콘솔에 등록된 콜백 URI"),
    state: str = Query(..., description="CSRF 방지 토큰 — 프론트가 생성·검증"),
    use_case: SocialLoginUseCase = Depends(get_social_login_use_case),
) -> AuthorizeUrlResponseSchema:
    try:
        result = use_case.authorize_url(
            AuthorizeUrlQuery(provider=provider, redirect_uri=redirect_uri, state=state)
        )
    except UnsupportedProviderError as error:
        raise HTTPException(status_code=404, detail=str(error))
    return AuthorizeUrlResponseSchema(authorize_url=result.authorize_url)


@social_login_router.post("/social/{provider}/login", response_model=SocialLoginResponseSchema)
async def login(
    provider: str,
    body: SocialLoginRequestSchema,
    use_case: SocialLoginUseCase = Depends(get_social_login_use_case),
) -> SocialLoginResponseSchema:
    try:
        result = await use_case.login(
            SocialLoginCommand(
                provider=provider,
                code=body.code,
                redirect_uri=body.redirect_uri,
                state=body.state,
                account_type=body.account_type,
            )
        )
    except UnsupportedProviderError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except EmailNotProvidedError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except OAuthExchangeError as error:
        raise HTTPException(status_code=502, detail=str(error))
    return SocialLoginResponseSchema(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        is_new_user=result.is_new_user,
        user=AuthenticatedUserSchema(
            id=result.user.id,
            email=result.user.email,
            name=result.user.name,
            account_type=result.user.account_type,
        ),
    )

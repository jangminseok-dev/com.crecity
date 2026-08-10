from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from auth.adapter.outbound.gateways.google_oauth_gateway import GoogleOAuthGateway
from auth.adapter.outbound.gateways.kakao_oauth_gateway import KakaoOAuthGateway
from auth.adapter.outbound.gateways.naver_oauth_gateway import NaverOAuthGateway
from auth.adapter.outbound.jwt_access_token_issuer import JwtAccessTokenIssuer
from auth.adapter.outbound.pg.social_identity_pg_repository import SocialIdentityPgRepository
from auth.adapter.outbound.pg.user_pg_repository import UserPgRepository
from auth.adapter.outbound.redis.refresh_token_redis_store import RefreshTokenRedisStore
from auth.app.ports.input.social_login_use_case import SocialLoginUseCase
from auth.app.ports.output.social_profile_gateway import SocialProfileGateway
from auth.app.use_cases.social_login_interactor import SocialLoginInteractor
from auth.domain.entities.social_identity_entity import SocialProvider
from core.config import (
    AUTH_ACCESS_TOKEN_TTL_SECONDS,
    AUTH_REFRESH_TOKEN_TTL_SECONDS,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    KAKAO_CLIENT_ID,
    KAKAO_CLIENT_SECRET,
    NAVER_CLIENT_ID,
    NAVER_CLIENT_SECRET,
)
from core.database import get_db
from core.key.secret_manager import get_secret_manager
from core.redis import get_redis


@lru_cache(maxsize=1)
def _access_token_issuer() -> JwtAccessTokenIssuer:
    # 발급 시크릿은 `.env.auth` 경계 — 토큰을 발급하는 프로세스만 명시 로드한다.
    secrets = get_secret_manager()
    secrets.load_auth_env()
    return JwtAccessTokenIssuer(
        secret=secrets.require("AUTH_JWT_SECRET"),
        ttl_seconds=AUTH_ACCESS_TOKEN_TTL_SECONDS,
    )


def _gateways() -> dict[SocialProvider, SocialProfileGateway]:
    return {
        SocialProvider.KAKAO: KakaoOAuthGateway(KAKAO_CLIENT_ID, KAKAO_CLIENT_SECRET),
        SocialProvider.NAVER: NaverOAuthGateway(NAVER_CLIENT_ID, NAVER_CLIENT_SECRET),
        SocialProvider.GOOGLE: GoogleOAuthGateway(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    }


def get_social_login_use_case(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> SocialLoginUseCase:
    return SocialLoginInteractor(
        gateways=_gateways(),
        users=UserPgRepository(session=db),
        identities=SocialIdentityPgRepository(session=db),
        refresh_tokens=RefreshTokenRedisStore(redis=redis),
        access_tokens=_access_token_issuer(),
        refresh_ttl_seconds=AUTH_REFRESH_TOKEN_TTL_SECONDS,
    )

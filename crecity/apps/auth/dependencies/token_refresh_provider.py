from __future__ import annotations

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from auth.adapter.outbound.pg.role_pg_repository import RolePgRepository
from auth.adapter.outbound.pg.user_pg_repository import UserPgRepository
from auth.adapter.outbound.redis.refresh_token_redis_store import RefreshTokenRedisStore
from auth.app.ports.input.token_refresh_use_case import TokenRefreshUseCase
from auth.app.use_cases.token_refresh_interactor import TokenRefreshInteractor
from auth.dependencies.social_login_provider import _access_token_issuer
from core.config import AUTH_REFRESH_TOKEN_TTL_SECONDS
from core.database import get_db
from core.redis import get_redis


def get_token_refresh_use_case(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TokenRefreshUseCase:
    return TokenRefreshInteractor(
        users=UserPgRepository(session=db),
        refresh_tokens=RefreshTokenRedisStore(redis=redis),
        access_tokens=_access_token_issuer(),
        roles=RolePgRepository(session=db),
        refresh_ttl_seconds=AUTH_REFRESH_TOKEN_TTL_SECONDS,
    )

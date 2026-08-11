from __future__ import annotations

from fastapi import Depends
from redis.asyncio import Redis

from auth.adapter.outbound.redis.refresh_token_redis_store import RefreshTokenRedisStore
from auth.app.ports.input.logout_use_case import LogoutUseCase
from auth.app.use_cases.logout_interactor import LogoutInteractor
from core.redis import get_redis


def get_logout_use_case(redis: Redis = Depends(get_redis)) -> LogoutUseCase:
    return LogoutInteractor(refresh_tokens=RefreshTokenRedisStore(redis=redis))

from __future__ import annotations

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from auth.adapter.outbound.pg.social_identity_pg_repository import SocialIdentityPgRepository
from auth.adapter.outbound.pg.user_pg_repository import UserPgRepository
from auth.adapter.outbound.redis.refresh_token_redis_store import RefreshTokenRedisStore
from auth.adapter.outbound.redis.user_revocation_redis_store import UserRevocationRedisStore
from auth.app.ports.input.account_deletion_use_case import AccountDeletionUseCase
from auth.app.use_cases.account_deletion_interactor import AccountDeletionInteractor
from core.config import AUTH_ACCESS_TOKEN_TTL_SECONDS
from core.database import get_db
from core.redis import get_redis
from hub.dependencies.active_order_provider import get_active_order_port
from hub.dependencies.credit_balance_provider import get_credit_balance_port
from hub.dependencies.profile_deactivation_provider import get_profile_deactivation_port


def get_account_deletion_use_case(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AccountDeletionUseCase:
    return AccountDeletionInteractor(
        users=UserPgRepository(session=db),
        identities=SocialIdentityPgRepository(session=db),
        refresh_tokens=RefreshTokenRedisStore(redis=redis),
        active_orders=get_active_order_port(),
        balances=get_credit_balance_port(),
        profiles=get_profile_deactivation_port(),
        revocations=UserRevocationRedisStore(),
        access_ttl_seconds=AUTH_ACCESS_TOKEN_TTL_SECONDS,
    )

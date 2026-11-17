from __future__ import annotations

from auth.app.ports.output.user_revocation_store import UserRevocationStore
from core.redis import get_redis

_KEY_PREFIX = "auth:revoked-user:"


class UserRevocationRedisStore(UserRevocationStore):
    """검증기는 앱 조립 시점(Redis 초기화 전)에 만들어지므로 클라이언트를 호출 시점에 얻는다."""

    async def revoke(self, user_id: int, ttl_seconds: int) -> None:
        redis = await get_redis()
        await redis.set(f"{_KEY_PREFIX}{user_id}", "1", ex=ttl_seconds)

    async def is_revoked(self, user_id: int) -> bool:
        redis = await get_redis()
        return await redis.exists(f"{_KEY_PREFIX}{user_id}") == 1

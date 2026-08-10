from hashlib import sha256

from redis.asyncio import Redis

from auth.app.ports.output.refresh_token_store import RefreshTokenStore

_KEY_PREFIX = "auth:refresh:"


def _key(token: str) -> str:
    # 토큰 원문을 저장소에 남기지 않는다 — 해시를 키로 쓴다
    return _KEY_PREFIX + sha256(token.encode()).hexdigest()


class RefreshTokenRedisStore(RefreshTokenStore):

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def save(self, token: str, user_id: int, ttl_seconds: int) -> None:
        await self._redis.set(_key(token), str(user_id), ex=ttl_seconds)

    async def pop(self, token: str) -> int | None:
        value = await self._redis.getdel(_key(token))
        return int(value) if value is not None else None

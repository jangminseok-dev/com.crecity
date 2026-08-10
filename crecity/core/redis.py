from __future__ import annotations

from redis.asyncio import Redis

from core.config import REDIS_URL

client: Redis | None = None


def init_redis() -> None:
    global client
    if client is not None:
        return
    client = Redis.from_url(REDIS_URL, decode_responses=True)


async def dispose_redis() -> None:
    global client
    if client is not None:
        await client.aclose()
        client = None


async def get_redis() -> Redis:
    if client is None:
        init_redis()
    if client is None:
        raise RuntimeError("Redis 클라이언트가 초기화되지 않았습니다.")
    return client

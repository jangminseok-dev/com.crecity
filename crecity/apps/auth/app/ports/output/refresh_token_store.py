from __future__ import annotations

from abc import ABC, abstractmethod


class RefreshTokenStore(ABC):
    """리프레시 토큰 저장소 포트 — TTL 만료·1회용 회전을 전제한다(Redis 구현)."""

    @abstractmethod
    async def save(self, token: str, user_id: int, ttl_seconds: int) -> None: ...

    @abstractmethod
    async def pop(self, token: str) -> int | None:
        """토큰을 소비(조회+삭제, 원자적)하고 소유 user_id를 돌려준다 — 없으면 None."""
        ...

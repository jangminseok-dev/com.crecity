from __future__ import annotations

from abc import ABC, abstractmethod


class UserRevocationStore(ABC):
    """탈퇴 계정 폐기 목록 — 무상태 JWT를 TTL 전에 무효화하는 유일한 수단.

    액세스 토큰은 서명만으로 검증되므로 탈퇴해도 TTL(30분)까지 살아 있다. 탈퇴 시 계정 id를
    액세스 TTL만큼 여기에 올리고, 검증기가 매 요청 확인한다. TTL이 지나면 토큰도 만료라 자연 소멸.
    """

    @abstractmethod
    async def revoke(self, user_id: int, ttl_seconds: int) -> None:
        """계정을 폐기 목록에 올린다 — ttl은 액세스 토큰 TTL과 같게."""
        ...

    @abstractmethod
    async def is_revoked(self, user_id: int) -> bool: ...

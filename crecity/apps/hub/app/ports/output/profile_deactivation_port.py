from __future__ import annotations

from abc import ABC, abstractmethod


class ProfileDeactivationPort(ABC):
    """프로필 비활성화 포트 — 구현은 creator가 제공하고 main.py가 조립한다.

    계정 삭제(§3.8) 시 공개 프로필이 남지 않도록 auth가 호출한다.
    """

    @abstractmethod
    async def deactivate_profile(self, user_id: int) -> None:
        """해당 계정의 프로필을 DELETED로 — 프로필이 없으면 아무 일도 하지 않는다."""
        ...

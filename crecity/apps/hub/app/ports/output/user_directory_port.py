from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.user_ref_dto import UserRef


class UserDirectoryPort(ABC):
    """회원 디렉토리 조회 포트 — 구현은 auth가 제공하고 main.py가 조립한다."""

    @abstractmethod
    async def get_user(self, user_id: int) -> UserRef | None:
        """회원 참조를 돌려준다 — 없으면 None."""
        ...

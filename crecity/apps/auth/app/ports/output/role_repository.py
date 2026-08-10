from __future__ import annotations

from abc import ABC, abstractmethod


class RoleRepository(ABC):
    """RBAC 조회·부여 포트 — 역할·권한의 정의는 시드(마이그레이션)가 소유한다."""

    @abstractmethod
    async def permissions_for_user(self, user_id: int) -> list[str]:
        """사용자의 권한 코드 목록 — user_roles → role_permissions → permissions 합집합."""
        ...

    @abstractmethod
    async def roles_for_user(self, user_id: int) -> list[str]:
        """사용자의 역할 이름 목록."""
        ...

    @abstractmethod
    async def grant_role(self, user_id: int, role_name: str) -> bool:
        """역할 부여(멱등) — 역할이 없으면 ValueError, 이미 부여됐으면 False."""
        ...

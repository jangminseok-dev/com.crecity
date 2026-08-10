from __future__ import annotations

from abc import ABC, abstractmethod

from auth.domain.entities.user_entity import User


class AccessTokenIssuer(ABC):
    """액세스 토큰 발급 포트 — 서명 방식(JWT)·키 관리는 어댑터 뒤에 숨긴다."""

    @abstractmethod
    def issue(self, user: User, roles: list[str], permissions: list[str]) -> str:
        """서명된 액세스 토큰을 발급한다 (CPU-bound).

        roles·permissions는 발급 시점 RBAC 스냅샷 — 검증 측은 토큰만으로 인가한다.
        """
        ...

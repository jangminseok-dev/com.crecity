from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Role:
    """역할 — 권한의 묶음. 사용자에게 부여된다(user_roles M:N)."""

    id: int
    name: str  # 예: "admin"
    description: str


@dataclass(frozen=True, slots=True)
class Permission:
    """권한 — 보호 대상 행위의 단위. 라우터 검사(require_permission)의 기준이다.

    코드 규약: "<도메인>.<행위>" (예: "profile.review").
    """

    id: int
    code: str
    description: str

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class RoleOrm(Base):
    """역할 — 권한의 묶음(정통 RBAC). 시드·마이그레이션으로만 늘어난다."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str] = mapped_column(String(200))


class PermissionOrm(Base):
    """권한 — 보호 행위 단위. 코드 규약 "<도메인>.<행위>" (예: profile.review)."""

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(200))


class RolePermissionOrm(Base):
    """역할 ↔ 권한 매핑 (M:N, 복합 PK — 대리키 불필요)."""

    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), primary_key=True)


class UserRoleOrm(Base):
    """사용자 ↔ 역할 부여 (M:N, 복합 PK). 부여 이력은 granted_at."""

    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

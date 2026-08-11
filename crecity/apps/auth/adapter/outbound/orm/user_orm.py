from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class UserOrm(Base):
    """회원 — 이메일이 계정 단위(unique)라 크리에이터/브랜드 겸용이 원천 차단된다."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    # AccountType 값 — CREATOR | BRAND
    account_type: Mapped[str] = mapped_column(String(20))
    # 탈퇴 시각(§3.8, 갭 #33) — 거래 기록 보존을 위해 행은 남기고 소프트 삭제한다
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

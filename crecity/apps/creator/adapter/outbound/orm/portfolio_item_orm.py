from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class PortfolioItemOrm(Base):
    """포트폴리오 사진 — creator_profiles에 종속(같은 앱 내부 FK)."""

    __tablename__ = "portfolio_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("creator_profiles.id"), index=True
    )
    file_name: Mapped[str] = mapped_column(String(120), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

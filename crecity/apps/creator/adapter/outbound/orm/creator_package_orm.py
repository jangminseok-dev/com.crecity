from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CreatorPackageOrm(Base):
    """가격 공개 판매 패키지 — creator_profiles에 종속(같은 앱 내부 FK)."""

    __tablename__ = "creator_packages"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("creator_profiles.id"), index=True
    )
    # PackagePlatform 값
    platform: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    price_krw: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

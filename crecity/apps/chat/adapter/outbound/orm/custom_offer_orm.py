from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CustomOfferOrm(Base):
    """커스텀 오퍼 — conversations에 종속(같은 앱 내부 FK). order_id는 논리 참조."""

    __tablename__ = "custom_offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    title: Mapped[str] = mapped_column(String(100))
    price_krw: Mapped[int] = mapped_column(BigInteger)
    # OfferStatus 값
    status: Mapped[str] = mapped_column(String(10))
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

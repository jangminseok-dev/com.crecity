from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class LedgerEntryOrm(Base):
    """원장 기입 — append-only(수정·삭제 없음). orders에 종속(같은 앱 내부 FK).

    user_id는 auth users 논리 참조 — PLATFORM_REVENUE는 NULL.
    """

    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    # LedgerEntryType 값 — 잔액 합산 필터(user_id + entry_type)에 쓰인다
    entry_type: Mapped[str] = mapped_column(String(30), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    amount_krw: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

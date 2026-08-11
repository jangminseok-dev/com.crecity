from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class WithdrawalOrm(Base):
    """인출 요청 — 계좌 정보는 요청 시점 스냅샷(이력 보존, 3NF 허용 예외).

    user_id는 auth users 논리 참조(스포크 경계 — DB FK 없음).
    """

    __tablename__ = "withdrawals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    amount_krw: Mapped[int] = mapped_column(BigInteger)
    tax_krw: Mapped[int] = mapped_column(BigInteger)
    payout_krw: Mapped[int] = mapped_column(BigInteger)
    bank_name: Mapped[str] = mapped_column(String(50))
    account_number: Mapped[str] = mapped_column(String(50))
    account_holder: Mapped[str] = mapped_column(String(50))
    # WithdrawalStatus 값 — 대기 목록 필터(status)에 쓰인다
    status: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

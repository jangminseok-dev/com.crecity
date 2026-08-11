from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class OrderAdjustmentOrm(Base):
    """진행 중 주문의 추가 금액 요청 — orders에 종속(같은 앱 내부 FK).

    수락은 추가 결제(payment 경유)로만 일어난다 — PAID가 되면 주문 금액이 증액된 상태다.
    """

    __tablename__ = "order_adjustments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    extra_amount_krw: Mapped[int] = mapped_column(BigInteger)
    reason: Mapped[str] = mapped_column(Text)
    # AdjustmentStatus 값 — 대기 중(REQUESTED) 중복 요청 차단에 쓰인다
    status: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

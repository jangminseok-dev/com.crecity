from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class DisputeOrm(Base):
    """분쟁 — 주문 하나에 여러 건이 쌓일 수 있으나 OPEN은 동시에 하나만(도메인 강제).

    판정 결과(resolution)와 판정자는 이 행의 속성이며, 주문 상태는 orders가 소유한다.
    """

    __tablename__ = "order_disputes"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    raised_by_user_id: Mapped[int] = mapped_column(index=True)  # auth 논리 참조(FK 없음)
    reason: Mapped[str] = mapped_column(String(2000))
    # DisputeStatus 값 (OPEN | RESOLVED)
    status: Mapped[str] = mapped_column(String(10), index=True)
    # DisputeResolution 값 (REFUND | RELEASE | DISMISS) — 판정 전에는 NULL
    resolution: Mapped[str | None] = mapped_column(String(10), nullable=True)
    resolved_by_user_id: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

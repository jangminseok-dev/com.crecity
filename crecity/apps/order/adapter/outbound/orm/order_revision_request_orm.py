from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class OrderRevisionRequestOrm(Base):
    """수정 요청 이력(갭 #84) — append-only. orders에 종속(같은 앱 내부 FK).

    피드백 본문이 주문에 남아 재작업의 근거·분쟁 판단 자료가 된다.
    횟수의 정본은 `orders.revisions_used`(도입 이전 요청 포함) — 여기는 본문 이력이다.
    """

    __tablename__ = "order_revision_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    # 요청이 나온 검토 단계(OrderStatus 값: DRAFT_REVIEW=초안, IN_REVIEW=최종)
    requested_in: Mapped[str] = mapped_column(String(20))
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

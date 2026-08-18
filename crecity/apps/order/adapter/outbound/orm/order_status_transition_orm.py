from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class OrderStatusTransitionOrm(Base):
    """주문 상태 전이 이력(갭 #79) — append-only. orders에 종속(같은 앱 내부 FK).

    전이 시각이 응답 지표(평균 수락 소요·응답률, 갭 #80)의 원천이다.
    최초 상태(PENDING_ACCEPT)는 행을 만들지 않는다 — 시작 시각은 orders.created_at이 정본이라
    복사하면 이행적 종속(3NF 위반)이 된다. 도입(2026-08-18) 이전 주문은 이력이 없다(소급 불가).
    """

    __tablename__ = "order_status_transitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    # OrderStatus 값 쌍 — 저장 시점의 DB 상태가 from(동시성에서도 참인 출처)
    from_status: Mapped[str] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20), index=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

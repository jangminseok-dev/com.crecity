from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class AdminReportOrm(Base):
    """어뷰징 신고(갭 #54) — 주문 밖에서 벌어진 일을 운영자가 받는 창구.

    target_type + target_id는 다형 참조다(프로필·대화방). 대상은 타 스포크 소유라
    DB FK를 걸지 않고 논리 참조로 둔다 — 스포크 경계 원칙.
    """

    __tablename__ = "admin_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_user_id: Mapped[int] = mapped_column(Integer, index=True)
    target_type: Mapped[str] = mapped_column(String(20), index=True)
    target_id: Mapped[int] = mapped_column(Integer, index=True)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), index=True)
    # 처리 결과 — 신고에 1:1 종속이라 별도 테이블을 두지 않는다
    resolution_note: Mapped[str] = mapped_column(Text, server_default="")
    resolved_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

from datetime import datetime

from sqlalchemy import DateTime, Integer, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ReviewOrm(Base):
    """리뷰 — 완료 주문당 1개(order_id unique). 타 스포크 id는 논리 참조(DB FK 없음)."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    brand_user_id: Mapped[int] = mapped_column(Integer, index=True)
    creator_user_id: Mapped[int] = mapped_column(Integer, index=True)
    # 3축 평점 1~5 — 범위는 도메인(validate_score)이 강제
    communication_score: Mapped[int] = mapped_column(SmallInteger)
    timeliness_score: Mapped[int] = mapped_column(SmallInteger)
    satisfaction_score: Mapped[int] = mapped_column(SmallInteger)
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

from datetime import datetime

from sqlalchemy import DateTime, Integer, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class BrandReviewOrm(Base):
    """브랜드 리뷰(갭 #83) — 크리에이터→브랜드 역방향 평가. 완료 주문당 1개(order_id unique).

    타 스포크 id는 논리 참조(DB FK 없음). 단일 종합 평점 — 브랜드 평가 축을 억지로
    3축에 맞추지 않는다(축이 늘어날 실수요가 생기면 그때 분리).
    """

    __tablename__ = "brand_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    brand_user_id: Mapped[int] = mapped_column(Integer, index=True)  # 평가 대상
    creator_user_id: Mapped[int] = mapped_column(Integer, index=True)  # 작성자
    score: Mapped[int] = mapped_column(SmallInteger)  # 1~5 — 범위는 도메인이 강제
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

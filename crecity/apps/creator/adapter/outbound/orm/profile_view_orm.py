from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ProfileViewDailyOrm(Base):
    """프로필 일별 조회수(갭 #57) — 방문 낱건이 아니라 (프로필, 날짜)당 한 행으로 센다.

    낱건 로그는 금세 커지는데 크리에이터가 보는 건 추이뿐이라 집계 행만 유지한다
    (UPSERT로 증가). 날짜는 서버 로컬 기준.
    """

    __tablename__ = "profile_view_daily"
    __table_args__ = (UniqueConstraint("profile_id", "view_date", name="uq_profile_view_day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("creator_profiles.id"), index=True)
    view_date: Mapped[date] = mapped_column(Date, index=True)
    view_count: Mapped[int] = mapped_column(Integer, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

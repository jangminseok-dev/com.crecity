from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class AudienceBreakdownOrm(Base):
    """오디언스 구간별 비율(§2.1-6, 갭 #67) — 채널 지표에 종속.

    연령·성별은 **다중값**이라 한 컬럼에 몰지 않고 행으로 편다(3NF).
    (지표, 축, 구간)당 한 행이며 비율은 퍼밀 정수다.
    """

    __tablename__ = "profile_audience_breakdown"
    __table_args__ = (
        UniqueConstraint("analytics_id", "dimension", "bucket", name="uq_audience_bucket"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    analytics_id: Mapped[int] = mapped_column(
        ForeignKey("profile_analytics.id", ondelete="CASCADE"), index=True
    )
    dimension: Mapped[str] = mapped_column(String(10))  # AGE | GENDER
    bucket: Mapped[str] = mapped_column(String(10))
    share_permille: Mapped[int] = mapped_column(Integer)

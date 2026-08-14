from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ProfileAnalyticsOrm(Base):
    """채널 분석 지표 — creator_profiles에 종속(같은 앱 내부 FK), 프로필당 플랫폼 1행.

    자가입력 + 스크린샷 인증(§9.2) — 재제출 시 갱신(upsert).
    """

    __tablename__ = "profile_analytics"
    __table_args__ = (UniqueConstraint("profile_id", "platform", name="uq_profile_analytics"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("creator_profiles.id"), index=True)
    # ANALYTICS_PLATFORMS 값
    platform: Mapped[str] = mapped_column(String(20))
    followers_count: Mapped[int] = mapped_column(BigInteger)
    # 참여율 ×10 정수(3.5% → 35) — 미입력 NULL
    engagement_permille: Mapped[int | None] = mapped_column(Integer, nullable=True)
    screenshot_file_name: Mapped[str] = mapped_column(String(100))
    # 주 오디언스 지역(§2.1-6, 갭 #67) — 단일 값이라 컬럼으로 둔다(연령·성별은 조인 테이블)
    top_audience_region: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

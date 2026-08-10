from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CreatorProfileOrm(Base):
    """크리에이터 프로필 — 슬러그가 공개 URL 단위(프로그래매틱 SEO)."""

    __tablename__ = "creator_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    # auth users 논리 참조 — 스포크 경계라 DB FK는 걸지 않는다. NULL은 소셜 로그인 도입 전 레거시
    user_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    slug: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    tagline: Mapped[str] = mapped_column(String(200))
    bio: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    primary_category: Mapped[str] = mapped_column(String(50), index=True)
    # ProfileStatus 값 — 목록 노출 필터(APPROVED)에 쓰인다
    status: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

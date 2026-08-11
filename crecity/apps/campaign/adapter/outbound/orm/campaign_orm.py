from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CampaignOrm(Base):
    """역경매 공고 — brand_user_id는 auth users 논리 참조(DB FK 없음)."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_user_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    # CampaignPlatform 값
    platform: Mapped[str] = mapped_column(String(20), index=True)
    budget_krw: Mapped[int] = mapped_column(BigInteger)
    # CampaignStatus 값 — OPEN 목록 필터에 쓰인다
    status: Mapped[str] = mapped_column(String(20), index=True)
    # 지원 마감일(선택) — 주기 스캔이 status + deadline_at으로 만료 대상을 찾는다
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 타겟팅(선택, §3.2) — 지원 자격 제한이 아니라 매칭 안내용 표시 필드
    target_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CampaignApplicationOrm(Base):
    """공고 지원 — campaigns에 종속(같은 앱 내부 FK), 공고당 크리에이터 1회."""

    __tablename__ = "campaign_applications"
    __table_args__ = (
        UniqueConstraint("campaign_id", "creator_user_id", name="uq_campaign_application"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    creator_user_id: Mapped[int] = mapped_column(Integer, index=True)
    message: Mapped[str] = mapped_column(Text)
    proposed_price_krw: Mapped[int] = mapped_column(BigInteger)
    # 수락(결제) 시 생성된 주문 — order 스포크 논리 참조(DB FK 없음), NULL이면 수락 가능
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

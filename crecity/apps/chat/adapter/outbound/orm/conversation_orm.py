from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ConversationOrm(Base):
    """대화방 — 브랜드↔크리에이터 쌍당 1개. user id들은 auth 논리 참조(DB FK 없음)."""

    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("brand_user_id", "creator_user_id", name="uq_conversation_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_user_id: Mapped[int] = mapped_column(Integer, index=True)
    creator_user_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MessageOrm(Base):
    """메시지 — conversations에 종속(같은 앱 내부 FK), append-only(분쟁 근거)."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    sender_user_id: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    # 사진 메시지 — /uploads/chat/<file_name> 정적 서빙, 없으면 NULL
    image_file_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class ConversationReadOrm(Base):
    """대화방 읽음 시각 — 참여자별 1행(갭 #35). 안 읽음 = 이 시각 이후 상대 메시지."""

    __tablename__ = "conversation_reads"

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

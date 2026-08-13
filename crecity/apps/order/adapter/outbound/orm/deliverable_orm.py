from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class DeliverableOrm(Base):
    """납품물 — append-only(수정·삭제 없음). orders에 종속(같은 앱 내부 FK).

    kind=FILE이면 file_name·original_name, kind=LINK면 url이 채워진다.
    """

    __tablename__ = "order_deliverables"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    # DeliverableKind 값 (FILE | LINK)
    kind: Mapped[str] = mapped_column(String(10))
    file_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # 게시물 본문(크리에이터가 붙여넣음) — 광고 표기 검수 대상. 판정 결과는 파생값이라 저장하지 않는다.
    caption: Mapped[str | None] = mapped_column(String(3000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

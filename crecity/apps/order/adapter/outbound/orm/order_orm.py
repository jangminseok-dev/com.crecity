from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class OrderOrm(Base):
    """주문 — 금액·수수료율·패키지 제목은 생성 시점 스냅샷(요율 소급 차단, §7-4).

    package_id·user_id들은 타 스포크 논리 참조(스포크 경계 — DB FK 없음).
    deadline_at은 현재 상태의 마감시각 — 주기 스캔(cron)이 만료 전이를 수행한다.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    package_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 커스텀 오퍼 주문은 NULL
    package_title: Mapped[str] = mapped_column(String(100))
    brand_user_id: Mapped[int] = mapped_column(Integer, index=True)
    creator_user_id: Mapped[int] = mapped_column(Integer, index=True)
    amount_krw: Mapped[int] = mapped_column(BigInteger)
    brand_fee_percent: Mapped[int] = mapped_column(Integer)
    creator_fee_percent: Mapped[int] = mapped_column(Integer)
    requirements: Mapped[str] = mapped_column(Text)
    # OrderStatus 값 — 만료 스캔 필터(status + deadline_at)에 쓰인다
    status: Mapped[str] = mapped_column(String(20), index=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

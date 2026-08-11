from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class PaymentIntentOrm(Base):
    """결제 의도 — PG 승인 기록의 정본(payment 소유, BOUNDARIES §3).

    package_id·brand_user_id·order_id는 타 스포크 논리 참조(DB FK 없음).
    """

    __tablename__ = "payment_intents"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 토스 orderId로 쓰는 우리 쪽 고유 문자열
    pg_order_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    package_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 커스텀 오퍼 결제는 NULL
    offer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 커스텀 오퍼(chat) 논리 참조
    # 캠페인 지원(campaign) 논리 참조 — 지원 수락 결제만 non-NULL
    application_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 주문 금액 변경 요청(order) 논리 참조 — 추가 결제만 non-NULL
    adjustment_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    brand_user_id: Mapped[int] = mapped_column(Integer, index=True)
    requirements: Mapped[str] = mapped_column(Text)
    amount_krw: Mapped[int] = mapped_column(BigInteger)
    # 체크아웃에서 확정한 크레딧 사용분 — PG 결제액 = amount_krw − credit_applied_krw
    credit_applied_krw: Mapped[int] = mapped_column(BigInteger, server_default="0")
    # PaymentIntentStatus 값
    status: Mapped[str] = mapped_column(String(20), index=True)
    payment_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PaymentIntentItemOrm(Base):
    """장바구니 결제 항목(§3.8) — 다중값 컬럼 대신 조인 테이블(3NF).

    package_id는 creator 패키지 논리 참조(DB FK 없음). 단건 결제는 항목이 없다.
    """

    __tablename__ = "payment_intent_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    intent_id: Mapped[int] = mapped_column(ForeignKey("payment_intents.id"), index=True)
    package_id: Mapped[int] = mapped_column(Integer)

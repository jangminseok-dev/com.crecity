from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class OfferStatus(StrEnum):
    PENDING = "PENDING"  # 결제 대기
    PAID = "PAID"  # 결제 완료 — 주문으로 전환됨


@dataclass(frozen=True, slots=True)
class CustomOffer:
    """커스텀 오퍼 — 협상 결과의 맞춤 가격 제안. conversations에 종속.

    수신자(브랜드)·제안자(크리에이터)는 대화방이 알고 있으므로 중복 저장하지 않는다(3NF).
    """

    id: int
    conversation_id: int
    title: str
    price_krw: int
    status: OfferStatus
    order_id: int | None = None  # 결제 완료 시 생성된 주문(타 스포크 논리 참조)
    created_at: datetime | None = None

    def is_payable(self) -> bool:
        return self.status is OfferStatus.PENDING

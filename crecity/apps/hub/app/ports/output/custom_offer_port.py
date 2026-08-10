from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.custom_offer_dto import CustomOfferSummary


class CustomOfferPort(ABC):
    """커스텀 오퍼 조회·확정 포트 — 구현은 chat이 제공하고 main.py가 조립한다.

    §3 결제 흐름의 커스텀 가격 변형: 채팅 협상 → 크리에이터가 오퍼 제시 →
    브랜드 결제 시 payment·order가 이 포트로 가격·당사자를 해석한다.
    """

    @abstractmethod
    async def get_payable_offer(self, offer_id: int) -> CustomOfferSummary | None:
        """결제 대기(PENDING) 오퍼만 반환 — 없거나 이미 결제됐으면 None."""

    @abstractmethod
    async def mark_paid(self, offer_id: int, order_id: int) -> None:
        """결제 완료 표시 — 주문 생성 후 payment가 호출한다(표시용, 재결제 차단)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.campaign_application_dto import CampaignApplicationSummary


class CampaignApplicationPort(ABC):
    """캠페인 지원 조회·확정 포트 — 구현은 campaign이 제공하고 main.py가 조립한다.

    §3 결제 흐름의 역경매 변형: 지원 수락 = 견적 결제 → 주문 생성.
    payment(결제 준비·확정 표시)와 order(가격·당사자 해석)가 소비한다.
    """

    @abstractmethod
    async def get_payable_application(
        self, application_id: int
    ) -> CampaignApplicationSummary | None:
        """아직 주문으로 이어지지 않은 지원만 반환 — 없거나 이미 결제됐으면 None."""

    @abstractmethod
    async def mark_paid(self, application_id: int, order_id: int) -> None:
        """결제 완료 표시(order_id 기록) — 주문 생성 후 payment가 호출한다(재결제 차단)."""

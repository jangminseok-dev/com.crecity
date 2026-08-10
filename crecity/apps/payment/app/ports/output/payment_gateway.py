from __future__ import annotations

from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    """PG 게이트웨이 포트 — 토스페이먼츠 구현이 뒤에 선다(§7-3: 포트 격리, 교체 가능)."""

    @abstractmethod
    async def confirm(self, payment_key: str, pg_order_id: str, amount_krw: int) -> None:
        """결제 승인(캡처).

        Raises:
            PaymentConfirmError: PG 거절·통신 실패.
        """
        ...

    @abstractmethod
    async def cancel(self, payment_key: str, reason: str) -> None:
        """승인된 결제 취소 — 승인 후 주문 생성 실패의 보정용.

        Raises:
            PaymentConfirmError: 취소 실패(운영 개입 필요 — 로그로 추적).
        """
        ...

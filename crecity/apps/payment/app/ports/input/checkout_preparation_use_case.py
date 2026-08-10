from __future__ import annotations

from abc import ABC, abstractmethod

from payment.app.dtos.checkout_preparation_dto import CheckoutCommand, CheckoutResult


class CheckoutPreparationUseCase(ABC):
    """결제 준비 유스케이스 — 결제창 호출 전에 서버가 금액을 확정한다(위변조 방지).

    §3 결제 흐름의 앞단: 의도(intent) 기록 → 프론트 결제창 → 승인(payment_confirmation).
    """

    @abstractmethod
    async def prepare(self, command: CheckoutCommand) -> CheckoutResult:
        """결제 의도를 기록하고 결제창 파라미터를 돌려준다.

        Raises:
            NotBrandAccountError: 브랜드 계정이 아님.
            PackageNotOrderableError: 패키지가 없거나 주문 불가.
        """
        ...

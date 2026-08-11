from __future__ import annotations

from abc import ABC, abstractmethod

from payment.app.dtos.checkout_preparation_dto import (
    ApplicationCheckoutCommand,
    CartCheckoutCommand,
    CheckoutCommand,
    CheckoutResult,
    OfferCheckoutCommand,
)


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

    @abstractmethod
    async def prepare_offer(self, command: OfferCheckoutCommand) -> CheckoutResult:
        """커스텀 오퍼 결제 준비 — 오퍼 수신 브랜드만 가능.

        Raises:
            NotBrandAccountError: 브랜드 계정이 아니거나 오퍼 수신 브랜드가 아님.
            PackageNotOrderableError: 오퍼가 없거나 이미 결제됨.
        """
        ...

    @abstractmethod
    async def prepare_cart(self, command: CartCheckoutCommand) -> CheckoutResult:
        """장바구니 일괄 결제 준비(§3.8) — 총액 = 패키지별 (가격+수수료) 합.

        Raises:
            NotBrandAccountError: 브랜드 계정이 아님.
            PackageNotOrderableError: 장바구니가 비었거나 주문 불가 패키지 포함.
        """
        ...

    @abstractmethod
    async def prepare_application(self, command: ApplicationCheckoutCommand) -> CheckoutResult:
        """캠페인 지원 수락 결제 준비 — 공고 소유 브랜드만 가능.

        Raises:
            NotBrandAccountError: 브랜드 계정이 아니거나 공고 소유 브랜드가 아님.
            PackageNotOrderableError: 지원이 없거나 이미 수락(결제)됨.
        """
        ...

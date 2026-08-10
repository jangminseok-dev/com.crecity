from __future__ import annotations

from abc import ABC, abstractmethod

from payment.app.dtos.payment_confirmation_dto import ConfirmCommand, ConfirmResult


class PaymentConfirmationUseCase(ABC):
    """결제 승인 유스케이스 — PG 승인 후 주문 생성(허브 계약)까지 잇는다.

    승인 후 주문 생성이 실패하면 PG 취소로 보정한다(§3 — 재시도 가능한 단일 보정).
    """

    @abstractmethod
    async def confirm(self, command: ConfirmCommand) -> ConfirmResult:
        """결제를 승인하고 주문을 생성한다.

        Raises:
            PaymentIntentNotFoundError: 결제 의도 없음.
            NotPaymentOwnerError: 본인 결제 아님.
            PaymentAlreadyProcessedError: 이미 처리됨.
            PaymentAmountMismatchError: 금액 불일치(위변조 의심).
            PaymentConfirmError: PG 승인 실패 또는 주문 생성 실패(취소 보정됨).
        """
        ...

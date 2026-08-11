from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.order_cancellation_dto import CancellationCommand
from order.app.dtos.order_result_dto import OrderResult


class OrderCancellationUseCase(ABC):
    """양측 합의 취소 유스케이스 — 규칙·행위자 검증은 도메인(Order)이 강제한다.

    모든 메서드 공통 Raises:
        OrderNotFoundError: 주문 없음.
        NotOrderActorError: 당사자 아님 또는 요청자 본인의 동의·거부 시도.
        InvalidOrderTransitionError: 취소 불가 상태·중복 요청·대기 요청 없음.
    """

    @abstractmethod
    async def request(self, command: CancellationCommand) -> OrderResult:
        """당사자 취소 요청 — 상대 동의 대기(주문 상태 유지)."""
        ...

    @abstractmethod
    async def consent(self, command: CancellationCommand) -> OrderResult:
        """상대방 동의 → CANCELLED (+브랜드 전액 크레딧 환불)."""
        ...

    @abstractmethod
    async def decline(self, command: CancellationCommand) -> OrderResult:
        """상대방 거부 → 요청 해제, 주문 계속 진행."""
        ...

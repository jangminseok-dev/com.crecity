from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.order_progress_dto import OrderTransitionCommand
from order.app.dtos.order_result_dto import OrderResult


class OrderProgressUseCase(ABC):
    """주문 상태 전이 유스케이스 — 상태머신 규칙은 도메인(Order)이 강제한다.

    모든 메서드 공통 Raises:
        OrderNotFoundError: 주문 없음.
        NotOrderActorError: 해당 전이의 권한자가 아님.
        InvalidOrderTransitionError: 현재 상태에서 허용되지 않는 전이.
    """

    @abstractmethod
    async def accept(self, command: OrderTransitionCommand) -> OrderResult:
        """크리에이터 수락 → IN_PROGRESS."""
        ...

    @abstractmethod
    async def reject(self, command: OrderTransitionCommand) -> OrderResult:
        """크리에이터 거절 → REFUNDED (+브랜드 크레딧 환불)."""
        ...

    @abstractmethod
    async def submit(self, command: OrderTransitionCommand) -> OrderResult:
        """크리에이터 제출 → IN_REVIEW (72h 검토 마감 시작)."""
        ...

    @abstractmethod
    async def request_revision(self, command: OrderTransitionCommand) -> OrderResult:
        """브랜드 수정 요청 → IN_PROGRESS (무제한 반복 가능)."""
        ...

    @abstractmethod
    async def approve(self, command: OrderTransitionCommand) -> OrderResult:
        """브랜드 승인 → COMPLETED (+크리에이터 적립·플랫폼 수수료 확정)."""
        ...

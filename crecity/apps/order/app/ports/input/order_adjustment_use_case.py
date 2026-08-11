from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.order_adjustment_dto import (
    AdjustmentListQuery,
    AdjustmentResult,
    DeclineAdjustmentCommand,
    RequestAdjustmentCommand,
)


class OrderAdjustmentUseCase(ABC):
    """진행 중 주문 금액 변경(§3.8·§6, 갭 #31) — 수락은 payment 경유 추가 결제다.

    공통 Raises:
        OrderNotFoundError: 주문 없음.
        NotOrderActorError: 권한자가 아님.
        InvalidOrderTransitionError: 진행 중 상태가 아님.
    """

    @abstractmethod
    async def request(self, command: RequestAdjustmentCommand) -> AdjustmentResult:
        """크리에이터 추가 금액 요청 — 대기 중 요청이 있으면 409.

        Raises:
            ValueError: 금액·사유 형식 위반.
            DuplicateAdjustmentError: 이미 대기 중인 요청 존재.
        """
        ...

    @abstractmethod
    async def decline(self, command: DeclineAdjustmentCommand) -> AdjustmentResult:
        """브랜드 거절.

        Raises:
            AdjustmentNotFoundError: 요청 없음.
            InvalidAdjustmentError: 이미 처리됨.
        """
        ...

    @abstractmethod
    async def list_by_order(self, query: AdjustmentListQuery) -> list[AdjustmentResult]:
        """주문의 요청 이력 — 당사자만(NotOrderParticipantError)."""
        ...

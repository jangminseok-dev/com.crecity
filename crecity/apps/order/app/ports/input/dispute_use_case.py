from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.dispute_dto import DisputeListQuery, DisputeResult, RaiseDisputeCommand


class DisputeUseCase(ABC):
    """분쟁 신고·조회 — 판정(운영자)은 허브 `DisputeResolutionPort` 몫이다."""

    @abstractmethod
    async def raise_dispute(self, command: RaiseDisputeCommand) -> DisputeResult:
        """분쟁 신고 — 진행 중·검토 중 주문의 당사자만, 대기 중 분쟁이 있으면 거부.

        Raises:
            OrderNotFoundError: 주문 없음.
            NotOrderActorError: 주문 당사자가 아님.
            InvalidOrderTransitionError: 신고 가능한 상태가 아니거나 이미 대기 중인 분쟁이 있음.
            ValueError: 사유 길이 위반.
        """
        ...

    @abstractmethod
    async def list_disputes(self, query: DisputeListQuery) -> list[DisputeResult]:
        """주문의 분쟁 이력(등록순) — 당사자만.

        Raises:
            OrderNotFoundError: 주문 없음.
            NotOrderParticipantError: 주문 당사자가 아님.
        """
        ...

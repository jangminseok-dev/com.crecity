from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.withdrawal_request_dto import WithdrawalRequestCommand, WithdrawalResult


class WithdrawalRequestUseCase(ABC):
    """크리에이터 적립금 인출 — 요청(잔액 차감과 원자적)과 내 내역 조회."""

    @abstractmethod
    async def request(self, command: WithdrawalRequestCommand) -> WithdrawalResult: ...

    @abstractmethod
    async def list_mine(self, user_id: int) -> list[WithdrawalResult]:
        """내 인출 내역 — 최신순."""
        ...

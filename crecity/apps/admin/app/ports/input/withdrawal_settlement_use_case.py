from __future__ import annotations

from abc import ABC, abstractmethod

from admin.app.dtos.withdrawal_settlement_dto import SettlementDecisionCommand
from hub.app.dtos.withdrawal_settlement_dto import AnnualPayoutSummary, WithdrawalSummary


class WithdrawalSettlementUseCase(ABC):
    """인출 운영 처리 — 대기 목록 조회와 완료/실패 결정(감사 기록 포함)."""

    @abstractmethod
    async def list_pending(self) -> list[WithdrawalSummary]: ...

    @abstractmethod
    async def annual_summary(self, year: int) -> list[AnnualPayoutSummary]:
        """연간 지급 집계 — 지급명세서 제출 자료(갭 #2)."""
        ...

    @abstractmethod
    async def settle(self, command: SettlementDecisionCommand) -> WithdrawalSummary: ...

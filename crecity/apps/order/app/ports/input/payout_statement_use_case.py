from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.payout_statement_dto import StatementQuery, StatementResult


class PayoutStatementUseCase(ABC):
    """지급명세서 — 크리에이터 본인의 연간 지급·원천징수 내역(갭 #2)."""

    @abstractmethod
    async def statement(self, query: StatementQuery) -> StatementResult:
        """지급일 기준 연간 명세 — 지급 완료된 인출만 집계한다(내역이 없으면 0원 명세)."""
        ...

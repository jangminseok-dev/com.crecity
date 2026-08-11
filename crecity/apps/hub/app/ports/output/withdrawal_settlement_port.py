from __future__ import annotations

from abc import ABC, abstractmethod

from hub.app.dtos.withdrawal_settlement_dto import WithdrawalSummary


class WithdrawalSettlementPort(ABC):
    """인출 운영 처리 포트 — 구현은 order가 제공하고 main.py가 조립한다.

    이체 실행 자체는 현재 운영자 수동(은행 이체) — 지급대행 API 연동 시
    payment 구현으로 교체될 수 있도록 계약만 고정한다.
    """

    @abstractmethod
    async def list_pending(self) -> list[WithdrawalSummary]:
        """REQUESTED 상태 인출 — 오래된 순."""
        ...

    @abstractmethod
    async def complete(self, withdrawal_id: int) -> WithdrawalSummary | None:
        """이체 완료 확정(PAID) — 없으면 None, 이미 처리됐으면 ValueError."""
        ...

    @abstractmethod
    async def fail(self, withdrawal_id: int) -> WithdrawalSummary | None:
        """이체 실패(FAILED) + 잔액 복원 기입(원자적) — 없으면 None, 이미 처리됐으면 ValueError."""
        ...

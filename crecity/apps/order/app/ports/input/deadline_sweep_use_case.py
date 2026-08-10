from __future__ import annotations

from abc import ABC, abstractmethod

from order.app.dtos.deadline_sweep_dto import SweepResult


class DeadlineSweepUseCase(ABC):
    """72h 마감 스캔 유스케이스 — HTTP 표면 없음, cron 스크립트가 주기 실행한다(BOUNDARIES §4).

    수락 만료 → 자동 환불 · 검토 만료 → 자동 승인. 크래시에 안전(마감시각 저장 방식).
    """

    @abstractmethod
    async def sweep(self) -> SweepResult:
        """마감이 지난 주문을 만료 전이시키고 결과를 돌려준다."""
        ...

from __future__ import annotations

from abc import ABC, abstractmethod


class LedgerRepository(ABC):
    """원장 조회 포트 — 기입(insert)은 OrderRepository가 전이와 원자적으로 수행한다."""

    @abstractmethod
    async def balance_krw(self, user_id: int) -> int:
        """사용자 잔액 = 적립성 기입 합(BALANCE_CREDIT_TYPES) — 추후 차감 유형 도입 시 확장."""
        ...

    @abstractmethod
    async def monthly_summary(
        self, user_id: int, year: int
    ) -> list[tuple[int, str, int, int]]:
        """연간 월별 기입 요약(리포트 #90) — (월, entry_type, 합계, 건수), 기입 있는 조합만."""
        ...
